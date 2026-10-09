from django.db import models
from django.conf import settings


class VoiceLog(models.Model):
    """لاگ هر تعامل صوتی کاربر"""
    business = models.ForeignKey(
        "accounts.Business", on_delete=models.CASCADE,
        related_name="voice_logs", verbose_name="کسب‌وکار",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="voice_logs",
        verbose_name="کاربر",
    )
    transcript = models.TextField("متن تبدیل‌شده", blank=True)
    reply = models.TextField("پاسخ دستیار", blank=True)
    actions = models.JSONField("عملیات انجام‌شده", default=list, blank=True)
    error = models.TextField("خطا", blank=True)
    duration_ms = models.PositiveIntegerField("مدت (میلی‌ثانیه)", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "لاگ صوتی"
        verbose_name_plural = "لاگ‌های صوتی"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.created_at:%Y-%m-%d %H:%M}"


class AIConversation(models.Model):
    """تاریخچه‌ی گفتگو با دستیار (برای حفظ context)"""
    business = models.ForeignKey(
        "accounts.Business", on_delete=models.CASCADE,
        related_name="ai_conversations", verbose_name="کسب‌وکار",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="ai_conversations", verbose_name="کاربر",
    )
    role = models.CharField("نقش", max_length=20,
                            choices=[("user", "کاربر"), ("assistant", "دستیار")])
    content = models.TextField("محتوا")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "گفتگوی AI"
        verbose_name_plural = "گفتگوهای AI"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"