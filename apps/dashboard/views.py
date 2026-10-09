from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .analytics import (
    summary, pipeline, weekly_activity,
    monthly_finance, top_customers,
)

from django.utils import timezone
from apps.crm.models import Task

@login_required
def home(request):
    business = getattr(request, "business", None) or getattr(request.user, "business", None)
    if not business:
        return redirect("/accounts/register/")

    # قیف فروش با درصد
    pipe = pipeline(business)
    max_count = max([p["count"] for p in pipe] or [1]) or 1
    for p in pipe:
        p["percent"] = int((p["count"] / max_count) * 100) if max_count else 0

    # پیگیری‌های امروز
    today = timezone.localdate()
    today_qs = Task.objects.filter(
        business=business, is_done=False, due_date=today
    )[:5]

    priority_map = {
        "کم": "low", "متوسط": "mid",
        "زیاد": "high", "فوری": "urgent",
    }
    today_tasks = [
        {
            "id": t.id, "title": t.title,
            "due_date": t.due_date,
            "priority": t.priority,
            "priority_class": priority_map.get(t.priority, "mid"),
            "is_done": t.is_done,
        }
        for t in today_qs
    ]

    return render(request, "dashboard/home.html", {
        "business": business,
        "stats": summary(business),
        "pipeline": pipe,
        "today_tasks": today_tasks,
    })


@login_required
def reports(request):
    business = getattr(request, "business", None) or getattr(request.user, "business", None)
    if not business:
        return redirect("/accounts/register/")
    return render(request, "dashboard/reports.html", {"business": business})



