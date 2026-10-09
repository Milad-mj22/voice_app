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


# ═══════════════════════════════════════════════
# STT (Speech-to-Text)
# ═══════════════════════════════════════════════
class OpenAI_STT(BaseSTT):

    async def transcribe(self, audio_bytes: bytes, language: str = "fa") -> str:
        """پیش‌فرض: webm (برای کروم/اندروید/فایرفاکس)"""
        return await self.transcribe_with_filename(
            audio_bytes, filename="voice.webm", language=language
        )



    async def transcribe_with_filename(
        self,
        audio_bytes: bytes,
        filename: str = "voice.webm",
        language: str = "fa",
    ) -> str:
        try:
            client = _client()
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            response = await client.audio.transcriptions.create(
                model=settings.AI_CONFIG["STT_MODEL"],
                file=audio_file,
                language=language,
                # ⭐ کلید هوشمندی: به Whisper بگو چه کلماتی ممکنه بشنوی
                prompt=(
                    "این یک دستور صوتی برای سیستم مدیریت کسب‌وکار برق مرداس است. "
                    "کلمات رایج: مشتری، پروژه، فرصت فروش، پیگیری، مالی، درآمد، هزینه، "
                    "شماره تماس، شرکت، قرارداد، فاکتور، جلسه، تماس، یادآوری، گزارش. "
                    "نام‌های فارسی مثل: علی، رضایی، محمدی، احمدی، حسینی. "
                    "دستوراتی مثل: ثبت کن، اضافه کن، پیگیری کن، گزارش بده، نشون بده."
                ),
                response_format="text",
                temperature=0,   # ⭐ خروجی دقیق‌تر
            )
            text = response if isinstance(response, str) else response.text
            return (text or "").strip()
        except Exception as exc:
            raise STTError(f"خطا در تبدیل صدا به متن: {exc}") from exc



# ═══════════════════════════════════════════════
# TTS (Text-to-Speech)
# ═══════════════════════════════════════════════
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
            # پاسخ generator sync هست، نه async
            audio = b"".join(response.iter_bytes())
            return audio
        except Exception as exc:
            raise TTSError(f"خطا در تبدیل متن به صدا: {exc}") from exc


# ═══════════════════════════════════════════════
# LLM (Chat + Function Calling)
# ═══════════════════════════════════════════════
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