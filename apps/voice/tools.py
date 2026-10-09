"""
ابزارهای قابل صدا زدن توسط AI
هر تابع یه dict برمی‌گردونه که به AI داده می‌شه
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from django.db.models import Q, Sum
from django.utils import timezone

from apps.crm.models import (
    Customer, Project, Opportunity, Task, Finance,
    Supplier, Colleague, Competitor, Strategy,
)


# ============================================================
# ثبت رکوردهای جدید
# ============================================================

def create_customer(business, user, title, phone="", company="", notes="", **kwargs):
    """ثبت مشتری جدید"""
    if not title:
        return {"ok": False, "error": "نام مشتری الزامی است."}
    obj = Customer.objects.create(
        business=business, created_by=user,
        title=title, phone=phone, company=company,
        notes=notes, status="جدید",
    )
    return {"ok": True, "id": obj.id, "message": f"مشتری «{title}» ثبت شد."}


def create_project(business, user, title, customer_name="", notes="", **kwargs):
    """ثبت پروژه جدید"""
    if not title:
        return {"ok": False, "error": "عنوان پروژه الزامی است."}
    customer = None
    if customer_name:
        customer = Customer.objects.filter(
            business=business, title__icontains=customer_name
        ).first()
    obj = Project.objects.create(
        business=business, created_by=user,
        title=title, customer=customer, notes=notes, status="جدید",
    )
    return {"ok": True, "id": obj.id, "message": f"پروژه «{title}» ثبت شد."}


def create_opportunity(business, user, title, customer_name="", amount=None, **kwargs):
    """ثبت فرصت فروش"""
    if not title:
        return {"ok": False, "error": "عنوان فرصت الزامی است."}
    customer = None
    if customer_name:
        customer = Customer.objects.filter(
            business=business, title__icontains=customer_name
        ).first()

    amt = _to_decimal(amount)
    obj = Opportunity.objects.create(
        business=business, created_by=user,
        title=title, customer=customer, amount=amt, stage="سرنخ",
    )
    return {"ok": True, "id": obj.id, "message": f"فرصت فروش «{title}» ثبت شد."}


def create_task(business, user, title, due_date=None, priority="متوسط", **kwargs):
    """ثبت پیگیری"""
    if not title:
        return {"ok": False, "error": "عنوان پیگیری الزامی است."}
    d = _to_date(due_date)
    if priority not in ["کم", "متوسط", "زیاد", "فوری"]:
        priority = "متوسط"
    obj = Task.objects.create(
        business=business, created_by=user,
        title=title, due_date=d, priority=priority, status="جدید",
    )
    return {"ok": True, "id": obj.id, "message": f"پیگیری «{title}» ثبت شد."}


def create_finance(business, user, title, amount, type="درآمد", category="", **kwargs):
    """ثبت تراکنش مالی"""
    if not title:
        return {"ok": False, "error": "عنوان تراکنش الزامی است."}
    amt = _to_decimal(amount) or Decimal("0")
    if type not in ["درآمد", "هزینه"]:
        type = "درآمد"
    obj = Finance.objects.create(
        business=business, created_by=user,
        title=title, amount=amt, type=type, category=category,
    )
    return {"ok": True, "id": obj.id,
            "message": f"تراکنش «{title}» به مبلغ {amt:,} تومان ثبت شد."}


# ============================================================
# جستجو
# ============================================================

def search_customer(business, query="", **kwargs):
    """جستجوی مشتری"""
    qs = Customer.objects.filter(business=business)
    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(phone__icontains=query) |
            Q(company__icontains=query)
        )
    results = [
        {"id": c.id, "title": c.title, "phone": c.phone, "company": c.company}
        for c in qs[:10]
    ]
    if not results:
        return {"ok": True, "count": 0, "message": "مشتری‌ای پیدا نشد."}
    return {"ok": True, "count": len(results), "results": results,
            "message": f"{len(results)} مشتری پیدا شد."}


# ============================================================
# گزارش‌ها
# ============================================================

def get_report(business, report_type="summary", **kwargs):
    """گزارش کلی یا نوع خاص"""
    if report_type == "customers":
        n = Customer.objects.filter(business=business).count()
        return {"ok": True, "message": f"{n} مشتری ثبت شده است."}

    if report_type == "tasks":
        n = Task.objects.filter(business=business, is_done=False).count()
        return {"ok": True, "message": f"{n} پیگیری باز دارید."}

    if report_type == "finance":
        income = Finance.objects.filter(
            business=business, type="درآمد"
        ).aggregate(s=Sum("amount"))["s"] or 0
        expense = Finance.objects.filter(
            business=business, type="هزینه"
        ).aggregate(s=Sum("amount"))["s"] or 0
        return {"ok": True,
                "message": f"درآمد: {income:,} تومان، هزینه: {expense:,} تومان، "
                           f"سود: {income - expense:,} تومان."}

    # خلاصه‌ی کلی
    return {"ok": True, "message":
        f"مشتری: {Customer.objects.filter(business=business).count()} | "
        f"پروژه: {Project.objects.filter(business=business).count()} | "
        f"فرصت: {Opportunity.objects.filter(business=business).count()} | "
        f"پیگیری باز: {Task.objects.filter(business=business, is_done=False).count()}"
    }


def get_tasks_today(business, **kwargs):
    """پیگیری‌های امروز"""
    today = timezone.localdate()
    qs = Task.objects.filter(business=business, due_date=today, is_done=False)
    if not qs.exists():
        return {"ok": True, "message": "امروز پیگیری‌ای نداری."}
    items = [f"• {t.title}" for t in qs[:5]]
    return {"ok": True, "message": f"{qs.count()} پیگیری امروز:\n" + "\n".join(items)}


# ============================================================
# کمکی‌ها
# ============================================================

def _to_decimal(v):
    if v is None or v == "":
        return None
    try:
        # حذف کاما و اعداد فارسی
        s = str(v).replace(",", "").replace("،", "").strip()
        s = s.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _to_date(v):
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        s = str(v).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ============================================================
# نقشه‌ی توابع و اسکیمای OpenAI
# ============================================================

# نام تابع → خود تابع
TOOL_FUNCTIONS = {
    "create_customer": create_customer,
    "create_project": create_project,
    "create_opportunity": create_opportunity,
    "create_task": create_task,
    "create_finance": create_finance,
    "search_customer": search_customer,
    "get_report": get_report,
    "get_tasks_today": get_tasks_today,
}


# اسکیمای ابزارها برای OpenAI
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "create_customer",
            "description": "ثبت مشتری جدید در سیستم",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "نام مشتری"},
                    "phone": {"type": "string", "description": "شماره تماس"},
                    "company": {"type": "string", "description": "نام شرکت"},
                    "notes": {"type": "string", "description": "یادداشت"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "ثبت پروژه جدید",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "عنوان پروژه"},
                    "customer_name": {"type": "string", "description": "نام مشتری مرتبط"},
                    "notes": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_opportunity",
            "description": "ثبت فرصت فروش جدید",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "customer_name": {"type": "string"},
                    "amount": {"type": "string", "description": "مبلغ به تومان"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "ثبت پیگیری جدید",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due_date": {"type": "string",
                                 "description": "تاریخ به فرمت YYYY-MM-DD"},
                    "priority": {"type": "string",
                                 "enum": ["کم", "متوسط", "زیاد", "فوری"]},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_finance",
            "description": "ثبت تراکنش مالی (درآمد یا هزینه)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "amount": {"type": "string"},
                    "type": {"type": "string", "enum": ["درآمد", "هزینه"]},
                    "category": {"type": "string"},
                },
                "required": ["title", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_customer",
            "description": "جستجوی مشتری بر اساس نام یا شماره",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_report",
            "description": "دریافت گزارش خلاصه از وضعیت کسب‌وکار",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["summary", "customers", "tasks", "finance"],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks_today",
            "description": "دریافت پیگیری‌های امروز",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]