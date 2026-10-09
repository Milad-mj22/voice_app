from abc import ABC, abstractmethod


class BaseSTT(ABC):
    """تبدیل صدا به متن"""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str = "fa") -> str:
        raise NotImplementedError

    async def transcribe_with_filename(
        self,
        audio_bytes: bytes,
        filename: str = "voice.webm",
        language: str = "fa",
    ) -> str:
        """پیش‌فرض: نام فایل رو نادیده بگیر"""
        return await self.transcribe(audio_bytes, language=language)


class BaseTTS(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        raise NotImplementedError


class BaseLLM(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        raise NotImplementedError