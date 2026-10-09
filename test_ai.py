"""
تست لایه‌ی AI
اجرا: python test_ai.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import asyncio
from core.ai import get_llm, get_tts


async def main():
    # ۱. تست LLM
    print("→ تست LLM...")
    llm = get_llm()
    result = await llm.chat([
        {"role": "user", "content": "سلام، تو کی هستی؟ در یک جمله جواب بده."}
    ])
    print("پاسخ LLM:", result["content"])
    print("tool_calls:", result["tool_calls"])

    # ۲. تست TTS
    print("\n→ تست TTS...")
    tts = get_tts()
    audio = await tts.synthesize("سلام، من دستیار مرداس هستم.")
    print(f"طول فایل صوتی: {len(audio)} بایت")
    with open("test_tts.mp3", "wb") as f:
        f.write(audio)
    print("فایل test_tts.mp3 ساخته شد. پخشش کن.")


if __name__ == "__main__":
    asyncio.run(main())