"""
تنظیمات پروژه مرداس
"""
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "assistant.mykaman.ir",
    "www.assistant.mykaman.ir",   # ⭐ اضافه کن
]


CSRF_TRUSTED_ORIGINS = [
    "https://assistant.mykaman.ir",
    "https://www.assistant.mykaman.ir",   # ⭐ اضافه کن
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# ---------- اپلیکیشن‌ها ----------
INSTALLED_APPS = [
    "daphne",                          # باید قبل از runserver باشه
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",

    # اپ‌های پروژه
    "apps.accounts",
    "apps.crm",
    "apps.voice",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # ← این رو اضافه کن
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # میان‌افزار تشخیص کسب‌وکار از URL
    "apps.accounts.middleware.BusinessMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.accounts.context_processors.business_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------- دیتابیس ----------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

# ---------- احراز هویت ----------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]



# ---------- بین‌المللی‌سازی (فقط فارسی) ----------
LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# ---------- فایل‌های استاتیک و مدیا ----------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- Channels (WebSocket) ----------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        # اگه بعداً Redis اضافه کردی:
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        # "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    }
}

# ---------- تنظیمات اختصاصی مرداس ----------
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "merdas.mykaman.ir")

# حداکثر حجم فایل صوتی برای STT (بایت)
VOICE_MAX_BYTES = 20 * 1024 * 1024   # ۲۰ مگابایت

# لایه‌ی ماژولار هوش مصنوعی
AI_CONFIG = {
    "STT_PROVIDER": "openai",
    "TTS_PROVIDER": "openai",
    "LLM_PROVIDER": "openai",
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    "STT_MODEL": "gpt-4o-transcribe",   # دقیق‌تر ولی گرون‌تر
    "LLM_MODEL": "gpt-4o",
    "TTS_MODEL": "tts-1",
    "TTS_VOICE": "nova",
    "LANGUAGE": "fa",
}


LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


VOICE_MAX_BYTES = 20 * 1024 * 1024   # ۲۰ مگابایت