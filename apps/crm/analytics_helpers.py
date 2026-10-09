"""
توابع کمکی گزارش‌ها (بدون وابستگی به dashboard)
"""
from calendar import monthrange
from django.db.models import Sum
from django.utils import timezone
from .models import Customer, Task, Finance


def _fa_month(m):
    return ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد",
            "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن",
            "اسفند"][m - 1]


def _fa_weekday(w):
    # پایتون: دوشنبه=0 ... یکشنبه=6
    return ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه",
            "جمعه", "شنبه", "یکشنبه"][w]


def monthly_finance(business, months=6):
    from datetime import timedelta
    today = timezone.localdate()
    result = []
    for i in range(months - 1, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        first = today.replace(year=y, month=m, day=1)
        last_day = monthrange(y, m)[1]
        last = today.replace(year=y, month=m, day=last_day)

        inc = Finance.objects.filter(
            business=business, type="درآمد",
            date__gte=first, date__lte=last
        ).aggregate(s=Sum("amount"))["s"] or 0
        exp = Finance.objects.filter(
            business=business, type="هزینه",
            date__gte=first, date__lte=last
        ).aggregate(s=Sum("amount"))["s"] or 0

        result.append({
            "label": _fa_month(m),
            "income": int(inc),
            "expense": int(exp),
        })
    return result


def weekly_activity(business):
    from datetime import timedelta
    today = timezone.localdate()
    days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        days.append({
            "date": d.isoformat(),
            "label": _fa_weekday(d.weekday()),
            "customers": Customer.objects.filter(
                business=business, created_at__date=d
            ).count(),
            "tasks": Task.objects.filter(
                business=business, created_at__date=d
            ).count(),
        })
    return days