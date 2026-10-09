"""
انتخاب provider مناسب از روی تنظیمات
"""
from django.conf import settings
from .base import BaseSTT, BaseTTS, BaseLLM
from .exceptions import ProviderNotFound


def get_stt() -> BaseSTT:
    provider = settings.AI_CONFIG["STT_PROVIDER"]
    if provider == "openai":
        from .openai_provider import OpenAI_STT
        return OpenAI_STT()
    # اینجا می‌تونی provider های دیگه اضافه کنی:
    # if provider == "local":
    #     from .local_provider import LocalWhisper_STT
    #     return LocalWhisper_STT()
    raise ProviderNotFound(f"STT provider ناشناخته: {provider}")


def get_tts() -> BaseTTS:
    provider = settings.AI_CONFIG["TTS_PROVIDER"]
    if provider == "openai":
        from .openai_provider import OpenAI_TTS
        return OpenAI_TTS()
    # if provider == "elevenlabs":
    #     from .elevenlabs_provider import ElevenLabs_TTS
    #     return ElevenLabs_TTS()
    raise ProviderNotFound(f"TTS provider ناشناخته: {provider}")


def get_llm() -> BaseLLM:
    provider = settings.AI_CONFIG["LLM_PROVIDER"]
    if provider == "openai":
        from .openai_provider import OpenAI_LLM
        return OpenAI_LLM()
    # if provider == "ollama":
    #     from .ollama_provider import Ollama_LLM
    #     return Ollama_LLM()
    raise ProviderNotFound(f"LLM provider ناشناخته: {provider}")