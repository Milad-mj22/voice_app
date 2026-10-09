"""
WebSocket Consumer برای دستیار صوتی
پروتکل پیام‌ها:
  → {"type": "start"}                     شروع ضبط
  → {"type": "audio", "data": "<base64>"} chunk صدا
  → {"type": "stop"}                      پایان ضبط

  ← {"type": "ready"}
  ← {"type": "transcript", "text": "..."}
  ← {"type": "action", "name": "...", "result": {...}}
  ← {"type": "reply_text", "text": "..."}
  ← {"type": "reply_audio", "data": "<base64>"}
  ← {"type": "error", "message": "..."}
"""
import base64
import json
import time
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.conf import settings
from core.ai import get_stt, get_tts
from .agent import VoiceAgent
from .models import VoiceLog


logger = logging.getLogger(__name__)


class VoiceConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        print(">>> WS connect — user:", self.user, "auth:", self.user.is_authenticated)

        if not self.user.is_authenticated:
            print(">>> WS reject: user not authenticated")
            await self.close(code=4001)
            return

        self.business = await self._get_business()
        print(">>> WS connect — business:", self.business)

        if not self.business:
            print(">>> WS reject: no business")
            await self.close(code=4002)
            return

        self.audio_chunks = []
        self.started_at = None
        await self.accept()
        await self.send(text_data=json.dumps({"type": "ready"}))
        print(">>> WS accept: ready sent")

        
    async def disconnect(self, code):
        self.audio_chunks = []

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data:
                msg = json.loads(text_data)
            else:
                # اگر بایت خام اومد، مستقیم chunk صدا حساب کن
                self.audio_chunks.append(bytes_data)
                return

            mtype = msg.get("type")

            if mtype == "start":
                self.audio_chunks = []
                self.started_at = time.time()
                await self._send({"type": "recording"})

            elif mtype == "audio":
                chunk_b64 = msg.get("data", "")
                if chunk_b64:
                    self.audio_chunks.append(base64.b64decode(chunk_b64))

            elif mtype == "stop":
                await self._process_voice()

        except Exception as exc:
            logger.exception("VoiceConsumer error")
            await self._send({"type": "error", "message": str(exc)})

    # ---------------- پردازش ----------------

    async def _process_voice(self):
        if not self.audio_chunks:
            await self._send({"type": "error", "message": "صدایی ضبط نشد."})
            return

        audio = b"".join(self.audio_chunks)
        self.audio_chunks = []

        if len(audio) > settings.VOICE_MAX_BYTES:
            await self._send({"type": "error", "message": "حجم صدا زیاد است."})
            return

        duration_ms = int((time.time() - (self.started_at or time.time())) * 1000)

        # ۱. STT
        try:
            stt = get_stt()
            transcript = await stt.transcribe(audio, language="fa")
        except Exception as exc:
            await self._save_log(error=f"STT: {exc}", duration_ms=duration_ms)
            await self._send({"type": "error", "message": "نتونستم صدا رو تشخیص بدم."})
            return

        if not transcript:
            await self._send({"type": "error", "message": "چیزی نفهمیدم، دوباره بگو."})
            return

        await self._send({"type": "transcript", "text": transcript})

        # ۲. Agent
        try:
            agent = VoiceAgent(business=self.business, user=self.user)
            result = await agent.handle(transcript)
        except Exception as exc:
            logger.exception("Agent error")
            await self._save_log(transcript=transcript, error=f"Agent: {exc}",
                                 duration_ms=duration_ms)
            await self._send({"type": "error", "message": "خطا در پردازش درخواست."})
            return

        # ارسال عملیات‌ها
        for act in result["actions"]:
            await self._send({
                "type": "action",
                "name": act["name"],
                "result": act["result"],
            })

        reply = result["reply"]

        # ۳. TTS
        try:
            tts = get_tts()
            audio_out = await tts.synthesize(reply)
            await self._send({
                "type": "reply_audio",
                "data": base64.b64encode(audio_out).decode(),
            })
        except Exception as exc:
            logger.warning(f"TTS error: {exc}")

        await self._send({"type": "reply_text", "text": reply})

        # ۴. ذخیره لاگ
        await self._save_log(
            transcript=transcript, reply=reply,
            actions=[a["name"] for a in result["actions"]],
            duration_ms=duration_ms,
        )

    # ---------------- کمکی ----------------

    async def _send(self, payload: dict):
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))

    @database_sync_to_async
    def _get_business(self):
        return getattr(self.user, "business", None)

    @database_sync_to_async
    def _save_log(self, transcript="", reply="", actions=None,
                  error="", duration_ms=0):
        VoiceLog.objects.create(
            business=self.business, user=self.user,
            transcript=transcript, reply=reply,
            actions=actions or [], error=error,
            duration_ms=duration_ms,
        )