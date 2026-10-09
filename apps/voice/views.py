"""
API دستیار صوتی — نسخه HTTP (بدون WebSocket)
"""
import base64
import logging
import time

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings

from apps.voice.tools import normalize_persian_text
from core.ai import get_stt, get_tts
from .agent import VoiceAgent
from .models import VoiceLog


logger = logging.getLogger(__name__)


def _detect_extension(audio_file):
    """تشخیص پسوند واقعی فایل صوتی"""
    content_type = (audio_file.content_type or "").lower()
    name = (audio_file.name or "").lower()

    if "webm" in content_type or name.endswith(".webm"):
        return "webm"
    if "mp4" in content_type or name.endswith(".m4a") or name.endswith(".mp4"):
        return "mp4"
    if "mpeg" in content_type or name.endswith(".mp3") or name.endswith(".mpga"):
        return "mp3"
    if "ogg" in content_type or name.endswith(".ogg") or name.endswith(".oga"):
        return "ogg"
    if "wav" in content_type or name.endswith(".wav"):
        return "wav"
    if "flac" in content_type or name.endswith(".flac"):
        return "flac"
    return "webm"  # پیش‌فرض


@login_required
@require_POST
@csrf_protect
def voice_api(request):
    started = time.time()

    business = getattr(request, "business", None) or getattr(request.user, "business", None)
    if not business:
        return JsonResponse({"ok": False, "error": "کسب‌وکار پیدا نشد."}, status=400)

    audio_file = request.FILES.get("audio")
    if not audio_file:
        return JsonResponse({"ok": False, "error": "فایل صوتی دریافت نشد."}, status=400)

    if audio_file.size > settings.VOICE_MAX_BYTES:
        return JsonResponse({"ok": False, "error": "حجم صدا زیاد است."}, status=400)

    audio_bytes = audio_file.read()

    # ═══ تشخیص پسوند ═══
    ext = _detect_extension(audio_file)
    filename = f"voice.{ext}"

    print(f">>> voice_api: orig_name={audio_file.name} ct={audio_file.content_type} "
          f"ext={ext} size={len(audio_bytes)}")

    # ═══ STT ═══
    try:
        from asgiref.sync import async_to_sync
        stt = get_stt()


        transcript = async_to_sync(stt.transcribe_with_filename)(
            audio_bytes, filename=filename, language="fa"
        )

        # ⭐ نرمال‌سازی متن
        transcript = normalize_persian_text(transcript)

        print(f">>> voice_api: normalized = {transcript}")



    except Exception as exc:
        logger.exception("STT error")
        _save_log(business, request.user, error=f"STT: {exc}")
        return JsonResponse(
            {"ok": False, "error": f"نتونستم صدا رو تشخیص بدم. ({ext})"},
            status=500,
        )

    if not transcript:
        return JsonResponse(
            {"ok": False, "error": "چیزی نفهمیدم، دوباره بگو."},
            status=200,
        )

    # ═══ Agent ═══
    try:
        from asgiref.sync import async_to_sync
        agent = VoiceAgent(business=business, user=request.user)
        result = async_to_sync(agent.handle)(transcript)
    except Exception as exc:
        logger.exception("Agent error")
        _save_log(business, request.user, transcript=transcript, error=f"Agent: {exc}")
        return JsonResponse({"ok": False, "error": "خطا در پردازش درخواست."}, status=500)

    reply = result.get("reply", "")
    actions = result.get("actions", [])

    # ═══ TTS ═══
    audio_b64 = ""
    try:
        from asgiref.sync import async_to_sync
        tts = get_tts()
        audio_out = async_to_sync(tts.synthesize)(reply)
        audio_b64 = base64.b64encode(audio_out).decode()
    except Exception as exc:
        logger.warning(f"TTS error: {exc}")

    # ═══ ذخیره لاگ ═══
    duration_ms = int((time.time() - started) * 1000)
    _save_log(
        business, request.user,
        transcript=transcript,
        reply=reply,
        actions=[a["name"] for a in actions],
        duration_ms=duration_ms,
    )

    return JsonResponse({
        "ok": True,
        "transcript": transcript,
        "reply": reply,
        "actions": [
            {"name": a["name"], "result": a.get("result", {})}
            for a in actions
        ],
        "audio": audio_b64,
        "duration_ms": duration_ms,
    })


def _save_log(business, user, transcript="", reply="", actions=None,
              error="", duration_ms=0):
    try:
        VoiceLog.objects.create(
            business=business, user=user,
            transcript=transcript, reply=reply,
            actions=actions or [], error=error,
            duration_ms=duration_ms,
        )
    except Exception:
        logger.exception("VoiceLog save failed")