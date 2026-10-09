"""
API ساده برای CRUD روی مدل‌های CRM
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import (
    Customer, Project, Opportunity, Task, Finance,
    Supplier, Colleague, Competitor, Strategy,
)


# ---------- نگاشت نوع → مدل ----------
TYPE_TO_MODEL = {
    "customer": Customer,
    "project": Project,
    "opportunity": Opportunity,
    "task": Task,
    "finance": Finance,
    "supplier": Supplier,
    "colleague": Colleague,
    "competitor": Competitor,
    "strategy": Strategy,
    # نام‌های ماژول‌ها به مدل‌ها
    "sales": Customer,
    "delivery": Project,
    "hr": Colleague,
    "operations": Supplier,
    "growth": Opportunity,
}

TYPE_LABELS = {
    "customer": "مشتری",
    "project": "پروژه",
    "opportunity": "فرصت فروش",
    "task": "پیگیری",
    "finance": "مالی",
    "supplier": "تأمین‌کننده",
    "colleague": "همکار",
    "competitor": "رقیب",
    "strategy": "استراتژی",
}


def _get_business(request):
    business = getattr(request, "business", None) or getattr(request.user, "business", None)
    return business


def _serialize(obj):
    """تبدیل رکورد به dict"""
    data = {
        "id": obj.id,
        "title": obj.title,
        "status": getattr(obj, "status", ""),
        "notes": getattr(obj, "notes", ""),
        "date": obj.date.isoformat() if getattr(obj, "date", None) else None,
        "created_at": obj.created_at.isoformat() if hasattr(obj, "created_at") else None,
    }
    # فیلدهای اختیاری
    for f in ("phone", "company", "email", "address", "amount", "type", "category",
              "priority", "is_done", "progress", "budget", "stage", "probability",
              "position", "website", "source", "tags"):
        if hasattr(obj, f):
            v = getattr(obj, f)
            if hasattr(v, "isoformat"):
                v = v.isoformat()
            elif v is not None and not isinstance(v, (str, int, float, bool, list, dict)):
                v = str(v)
            data[f] = v
    return data


# ============================================================
# لیست / ساخت
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def records_view(request, record_type):
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)

    model = TYPE_TO_MODEL.get(record_type)
    if not model:
        return JsonResponse({"error": "نوع نامعتبر."}, status=404)

    if request.method == "GET":
        qs = model.objects.filter(business=business)
        return JsonResponse([_serialize(o) for o in qs], safe=False)

    # POST
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON نامعتبر."}, status=400)

    title = (body.get("title") or "").strip()
    if not title:
        return JsonResponse({"error": "عنوان الزامی است."}, status=400)

    fields = {"business": business, "created_by": request.user, "title": title}
    for f in ("status", "notes", "phone", "company", "email", "address",
              "category", "priority", "stage", "type", "position", "website",
              "source", "tags"):
        if f in body and hasattr(model, f):
            fields[f] = body[f]
    if body.get("date"):
        fields["date"] = body["date"]

    obj = model.objects.create(**fields)
    return JsonResponse(_serialize(obj), status=201)


# ============================================================
# جزئیات / ویرایش / حذف
# ============================================================

@login_required
@require_http_methods(["GET", "PUT", "DELETE"])
@csrf_protect
def record_detail_view(request, record_type, pk):
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)

    model = TYPE_TO_MODEL.get(record_type)
    if not model:
        return JsonResponse({"error": "نوع نامعتبر."}, status=404)

    obj = get_object_or_404(model, pk=pk, business=business)

    if request.method == "GET":
        return JsonResponse(_serialize(obj))

    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({"ok": True})

    # PUT
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON نامعتبر."}, status=400)

    for f in ("title", "status", "notes", "phone", "company", "email",
              "address", "category", "priority", "stage", "type", "position",
              "website", "source", "tags"):
        if f in body and hasattr(model, f):
            setattr(obj, f, body[f])
    if "date" in body:
        obj.date = body["date"] or None

    obj.save()
    return JsonResponse(_serialize(obj))


# ============================================================
# آمار
# ============================================================

@login_required
def stats_view(request):
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)
    return JsonResponse({
        "customers": Customer.objects.filter(business=business).count(),
        "projects": Project.objects.filter(business=business).count(),
        "opportunities": Opportunity.objects.filter(business=business).count(),
        "tasks": Task.objects.filter(business=business, is_done=False).count(),
    })


# ============================================================
# جستجوی سراسری
# ============================================================

@login_required
def search_view(request):
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)

    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([])

    results = []
    for tkey, model in [
        ("customer", Customer),
        ("project", Project),
        ("opportunity", Opportunity),
        ("task", Task),
        ("finance", Finance),
    ]:
        qs = model.objects.filter(business=business).filter(
            Q(title__icontains=q) |
            Q(notes__icontains=q) |
            Q(company__icontains=q) if hasattr(model, "company") else Q(title__icontains=q)
        )[:10]
        for obj in qs:
            results.append({
                "id": obj.id,
                "title": obj.title,
                "type": tkey,
                "type_label": TYPE_LABELS.get(tkey, tkey),
                "company": getattr(obj, "company", "") or "",
            })
    return JsonResponse(results, safe=False)


# ============================================================
# خروجی JSON (پشتیبان)
# ============================================================

@login_required
def export_view(request):
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)

    data = {}
    for tkey, model in TYPE_TO_MODEL.items():
        if tkey not in data:
            data[tkey] = [_serialize(o) for o in model.objects.filter(business=business)]

    payload = {
        "version": 1,
        "business": business.name,
        "exported_at": __import__("datetime").datetime.now().isoformat(),
        "data": data,
    }
    resp = HttpResponse(
        json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    resp["Content-Disposition"] = f'attachment; filename="backup-{business.slug}.json"'
    return resp




# ═══════════════════════════════════════════
# API گزارش‌ها
# ═══════════════════════════════════════════

@login_required
def report_pipeline_view(request):
    """قیف فروش"""
    from django.db.models import Sum
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)

    stages = ["سرنخ", "تماس اولیه", "نیازسنجی", "ارائه پیشنهاد",
              "مذاکره", "برنده", "باخت"]
    result = []
    for st in stages:
        qs = Opportunity.objects.filter(business=business, stage=st)
        result.append({
            "stage": st,
            "count": qs.count(),
            "amount": int(qs.aggregate(s=Sum("amount"))["s"] or 0),
        })
    return JsonResponse(result, safe=False)


@login_required
def report_monthly_view(request):
    """روند مالی ۶ ماه"""
    from .analytics_helpers import monthly_finance
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)
    return JsonResponse(monthly_finance(business, months=6), safe=False)


@login_required
def report_weekly_view(request):
    """فعالیت هفتگی"""
    from .analytics_helpers import weekly_activity
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)
    return JsonResponse(weekly_activity(business), safe=False)


@login_required
def report_top_customers_view(request):
    """مشتریان برتر"""
    from django.db.models import Sum, Q
    business = _get_business(request)
    if not business:
        return JsonResponse({"error": "کسب‌وکار پیدا نشد."}, status=400)

    qs = Customer.objects.filter(business=business).annotate(
        total=Sum("transactions__amount",
                  filter=Q(transactions__type="درآمد"))
    ).filter(total__gt=0).order_by("-total")[:5]

    return JsonResponse(
        [{"title": c.title, "total": int(c.total or 0)} for c in qs],
        safe=False,
    )