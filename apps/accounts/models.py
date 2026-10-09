from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class Business(models.Model):
    """هر کسب‌وکار یک پنل اختصاصی داره"""
    name = models.CharField("نام کسب‌وکار", max_length=100)
    slug = models.SlugField("شناسه URL", max_length=60, unique=True)
    logo = models.ImageField("لوگو", upload_to="logos/", blank=True, null=True)
    brand_color = models.CharField("رنگ برند", max_length=7, default="#2563eb")
    phone = models.CharField("تلفن", max_length=20, blank=True)
    address = models.TextField("آدرس", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "کسب‌وکار"
        verbose_name_plural = "کسب‌وکارها"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class User(AbstractUser):
    """کاربر سیستم — هر کاربر به یک کسب‌وکار تعلق داره"""

    ROLE_CHOICES = [
        ("owner", "مالک"),
        ("admin", "مدیر"),
        ("sales", "فروش"),
        ("accountant", "حسابدار"),
        ("viewer", "بیننده"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="users",
        null=True, blank=True,
        verbose_name="کسب‌وکار",
    )
    role = models.CharField(
        "نقش", max_length=20, choices=ROLE_CHOICES, default="owner"
    )
    phone = models.CharField("موبایل", max_length=15, blank=True)

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.get_full_name() or self.username