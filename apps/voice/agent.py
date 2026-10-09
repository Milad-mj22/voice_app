"""
Agent دستیار صوتی مرداس
LLM رو صدا می‌زنه، اگه tool_call داشت اجرا می‌کنه،
نتیجه رو دوباره به LLM می‌ده تا پاسخ نهایی بسازه
"""
import json
from channels.db import database_sync_to_async

from core.ai import get_llm
from core.ai.prompts import SYSTEM_PROMPT
from .tools import TOOLS_SCHEMA, TOOL_FUNCTIONS
from .models import AIConversation


MAX_TOOL_ROUNDS = 3


class VoiceAgent:
    def __init__(self, business, user):
        self.business = business
        self.user = user
        self.llm = get_llm()

    async def handle(self, user_text: str) -> dict:
        """ورودی: متن کاربر / خروجی: {"reply": "...", "actions": [...]}"""
        actions = []

        # ۱. گرفتن تاریخچه (async-safe)
        history = await self._get_history()

        # ۲. ذخیره‌ی پیام کاربر (async-safe)
        await self._save_message("user", user_text)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})

        reply = ""

        for _ in range(MAX_TOOL_ROUNDS):
            result = await self.llm.chat(messages, tools=TOOLS_SCHEMA)

            if result["tool_calls"]:
                messages.append({
                    "role": "assistant",
                    "content": result["content"] or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                            },
                        }
                        for tc in result["tool_calls"]
                    ],
                })

                for tc in result["tool_calls"]:
                    tool_result = await self._run_tool(tc["name"], tc["arguments"])
                    actions.append({
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                        "result": tool_result,
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    })
                continue

            reply = result["content"] or "متوجه نشدم، دوباره بگو."
            break
        else:
            reply = reply or "متأسفانه نتونستم عملیات رو تکمیل کنم."

        # ۳. ذخیره‌ی پاسخ دستیار (async-safe)
        await self._save_message("assistant", reply)

        return {"reply": reply, "actions": actions}

    # ---------------- sync→async wrappers ----------------

    @database_sync_to_async
    def _get_history(self):
        qs = AIConversation.objects.filter(
            business=self.business, user=self.user
        ).order_by("-created_at")[:10]
        return [
            {"role": c.role, "content": c.content}
            for c in reversed(list(qs))
        ]

    @database_sync_to_async
    def _save_message(self, role, content):
        AIConversation.objects.create(
            business=self.business, user=self.user,
            role=role, content=content,
        )

    @database_sync_to_async
    def _run_tool(self, name: str, args: dict) -> dict:
        func = TOOL_FUNCTIONS.get(name)
        if not func:
            return {"ok": False, "error": f"تابع {name} پیدا نشد."}
        try:
            return func(business=self.business, user=self.user, **args)
        except Exception as exc:
            return {"ok": False, "error": f"خطا در اجرای {name}: {exc}"}