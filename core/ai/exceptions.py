class AIError(Exception):
    """خطای پایه‌ی لایه‌ی AI"""
    pass


class STTError(AIError):
    """خطا در تبدیل صدا به متن"""
    pass


class TTSError(AIError):
    """خطا در تبدیل متن به صدا"""
    pass


class LLMError(AIError):
    """خطا در ارتباط با مدل زبانی"""
    pass


class ProviderNotFound(AIError):
    """provider انتخاب‌شده پیدا نشد"""
    pass