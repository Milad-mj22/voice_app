"""
پیاده‌سازی provider های OpenAI
"""
import io
import json
from openai import AsyncOpenAI
from contextlib import asynccontextmanager

from django.conf import settings
from .base import BaseSTT, BaseTTS, BaseLLM
from .exceptions import STTError, TTSError, LLMError


# ═══════════════════════════════════════════════
# کلاینت context-manager (هر بار ساخته می‌شه، بسته می‌شه)
# ═══════════════════════════════════════════════
@asynccontextmanager
async def _client():
    client = AsyncOpenAI(api_key=settings.AI_CONFIG["OPENAI_API_KEY"])
    try:
        yield client
    finally:
        try:
            await client.close()
        except Exception:
            pass


# ═══════════════════════════════════════════════
# STT
# ═══════════════════════════════════════════════
class OpenAI_STT(BaseSTT):

    async def transcribe(self, audio_bytes: bytes, language: str = "fa") -> str:
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
            async with _client() as client:
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = filename

                response = await client.audio.transcriptions.create(
                    model=settings.AI_CONFIG["STT_MODEL"],
                    file=audio_file,
                    language=language,
                    prompt=(
                        "این یک دستور صوتی برای سیستم مدیریت کسب‌وکار است. "
                        "شماره‌های تلفن به فارسی گفته می‌شن: صفر، یک، دو، سه، چهار، پنج، شش، هفت، هشت، نُه. "
                        "مثال: «صفر نه یک دو سه چهار پنج شش هفت هشت نه» = 09123456789. "
                        "اعداد را حتماً به رقم بنویس، نه به حروف. "
                        "کلمات رایج: مشتری، پروژه، فرصت فروش، پیگیری، مالی، شماره تماس، "
                        "تلفن، موبایل، شرکت، ثبت، اضافه، گزارش."
                    ),
                    response_format="text",
                    temperature=0,
                )
                text = response if isinstance(response, str) else response.text
                return (text or "").strip()
        except Exception as exc:
            raise STTError(f"خطا در تبدیل صدا به متن: {exc}") from exc


# ═══════════════════════════════════════════════
# TTS
# ═══════════════════════════════════════════════
class OpenAI_TTS(BaseTTS):

    async def synthesize(self, text: str) -> bytes:
        try:
            async with _client() as client:
                response = await client.audio.speech.create(
                    model=settings.AI_CONFIG["TTS_MODEL"],
                    voice=settings.AI_CONFIG["TTS_VOICE"],
                    input=text,
                    response_format="mp3",
                )
                audio = b"".join(response.iter_bytes())
                return audio
        except Exception as exc:
            raise TTSError(f"خطا در تبدیل متن به صدا: {exc}") from exc


# ═══════════════════════════════════════════════
# LLM
# ═══════════════════════════════════════════════
class OpenAI_LLM(BaseLLM):

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        try:
            async with _client() as client:
                kwargs = {
                    "model": settings.AI_CONFIG["LLM_MODEL"],
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