"""
کلاس‌های انتزاعی لایه‌ی AI
هر provider جدید باید این کلاس‌ها رو پیاده کنه
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseSTT(ABC):
    """تبدیل صدا به متن (Speech-to-Text)"""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str = "fa") -> str:
        """
        ورودی: بایت‌های فایل صوتی
        خروجی: متن فارسی
        """
        raise NotImplementedError


class BaseTTS(ABC):
    """تبدیل متن به صدا (Text-to-Speech)"""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        ورودی: متن فارسی
        خروجی: بایت‌های فایل صوتی (mp3)
        """
        raise NotImplementedError


class BaseLLM(ABC):
    """مدل زبانی (Chat / Function Calling)"""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        ورودی:
            messages: تاریخچه‌ی پیام‌ها [{"role": "user", "content": "..."}]
            tools: لیست توابع قابل صدا زدن (اختیاری)
        خروجی:
            {
                "content": "پاسخ متنی مدل",
                "tool_calls": [{"name": "...", "arguments": {...}}] یا []
            }
        """
        raise NotImplementedError