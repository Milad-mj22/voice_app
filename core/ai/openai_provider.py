"""
پیاده‌سازی provider های OpenAI
"""
import io
import json
from openai import AsyncOpenAI

from django.conf import settings
from .base import BaseSTT, BaseTTS, BaseLLM
from .exceptions import STTError, TTSError, LLMError


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.AI_CONFIG["OPENAI_API_KEY"])


# ---------- STT ----------
class OpenAI_STT(BaseSTT):
    async def transcribe(self, audio_bytes: bytes, language: str = "fa") -> str:
        try:
            client = _client()
            # Whisper یه فایل با پسوند می‌خواد → از BytesIO استفاده می‌کنیم
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "voice.webm"

            response = await client.audio.transcriptions.create(
                model=settings.AI_CONFIG["STT_MODEL"],   # whisper-1
                file=audio_file,
                language=language,
                response_format="text",
            )
            # response گاهی مستقیم رشته‌ست
            text = response if isinstance(response, str) else response.text
            return (text or "").strip()
        except Exception as exc:
            raise STTError(f"خطا در تبدیل صدا به متن: {exc}") from exc


# ---------- TTS ----------
# ---------- TTS ----------
class OpenAI_TTS(BaseTTS):
    async def synthesize(self, text: str) -> bytes:
        try:
            client = _client()
            response = await client.audio.speech.create(
                model=settings.AI_CONFIG["TTS_MODEL"],   # tts-1
                voice=settings.AI_CONFIG["TTS_VOICE"],   # alloy
                input=text,
                response_format="mp3",
            )
            # پاسخ به صورت generator sync هست، نه async
            audio = b"".join(response.iter_bytes())
            return audio
        except Exception as exc:
            raise TTSError(f"خطا در تبدیل متن به صدا: {exc}") from exc
# ---------- LLM ----------
class OpenAI_LLM(BaseLLM):
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        try:
            client = _client()
            kwargs = {
                "model": settings.AI_CONFIG["LLM_MODEL"],   # gpt-4o
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await client.chat.completions.create(**kwargs)
            msg = response.choices[0].message

            result = {
                "content": msg.content or "",
                "tool_calls": [],
            }

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    result["tool_calls"].append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": args,
                    })

            return result
        except Exception as exc:
            raise LLMError(f"خطا در ارتباط با مدل زبانی: {exc}") from exc