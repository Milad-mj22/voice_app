"""
توابع محاسبه‌ی آمار و گزارش‌ها
"""
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.crm.models import (
    Customer, Project, Opportunity, Task, Finance, Colleague
)


def summary(business):
    """خلاصه‌ی کلی"""
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    income = Finance.objects.filter(
        business=business, type="درآمد"
    ).aggregate(s=Sum("amount"))["s"] or Decimal("0")

    expense = Finance.objects.filter(
        business=business, type="هزینه"
    ).aggregate(s=Sum("amount"))["s"] or Decimal("0")

    return {
        "customers_total": Customer.objects.filter(business=business).count(),
        "customers_new_week": Customer.objects.filter(
            business=business, created_at__gte=week_ago
        ).count(),
        "projects_active": Project.objects.filter(
            business=business, status="فعال"
        ).count(),
        "opportunities_open": Opportunity.objects.filter(
            business=business
        ).exclude(stage__in=["برنده", "باخت"]).count(),
        "tasks_open": Task.objects.filter(
            business=business, is_done=False
        ).count(),
        "tasks_overdue": Task.objects.filter(
            business=business, is_done=False, due_date__lt=today
        ).count(),
        "tasks_today": Task.objects.filter(
            business=business, is_done=False, due_date=today
        ).count(),
        "income": income,
        "expense": expense,
        "profit": income - expense,
        "colleagues": Colleague.objects.filter(business=business).count(),
    }


def pipeline(business):
    """قیف فروش — تعداد فرصت‌ها در هر مرحله"""
    stages = ["سرنخ", "تماس اولیه", "نیازسنجی", "ارائه پیشنهاد",
              "مذاکره", "برنده", "باخت"]
    result = []
    for stage in stages:
        qs = Opportunity.objects.filter(business=business, stage=stage)
        result.append({
            "stage": stage,
            "count": qs.count(),
            "amount": qs.aggregate(s=Sum("amount"))["s"] or 0,
        })
    return result


def weekly_activity(business):
    """فعالیت ۷ روز اخیر"""
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


def monthly_finance(business, months=6):
    """مالی ۶ ماه اخیر"""
    from calendar import monthrange
    today = timezone.localdate()
    result = []
    for i in range(months - 1, -1, -1):
        # محاسبه‌ی ماه i ماه قبل
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


def top_customers(business, limit=5):
    """مشتریان برتر بر اساس تراکنش"""
    qs = Customer.objects.filter(business=business).annotate(
        total=Sum("transactions__amount",
                  filter=Q(transactions__type="درآمد"))
    ).filter(total__gt=0).order_by("-total")[:limit]
    return [{"title": c.title, "total": int(c.total or 0)} for c in qs]


# ---------- کمکی ----------
def _fa_weekday(w):
    return ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه",
            "جمعه", "شنبه", "یکشنبه"][w]


def _fa_month(m):
    return ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد",
            "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن",
            "اسفند"][m - 1]