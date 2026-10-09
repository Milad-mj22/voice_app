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






def update_customer(business, user, customer_name, phone=None, **kwargs):
    """ویرایش مشتری موجود"""
    if not customer_name:
        return {"ok": False, "error": "نام مشتری رو بگو."}

    customer = Customer.objects.filter(
        business=business, title__icontains=customer_name
    ).first()

    if not customer:
        return {"ok": False, "error": f"مشتری «{customer_name}» پیدا نشد."}

    if phone:
        # نرمال‌سازی شماره
        phone = _normalize_phone(phone)
        customer.phone = phone

    customer.save()
    return {"ok": True, "message": f"اطلاعات مشتری «{customer.title}» ویرایش شد."}



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
    "update_customer": update_customer,
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

{
    "type": "function",
    "function": {
        "name": "update_customer",
        "description": "ویرایش اطلاعات مشتری موجود (مثل شماره تلفن)",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "description": "نام مشتری"},
                "phone": {"type": "string", "description": "شماره تماس جدید"},
            },
            "required": ["customer_name"],
        },
    },
},

]




import re

# ═══════════════════════════════════════
# نرمال‌سازی متن Whisper
# ═══════════════════════════════════════

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ENGLISH_DIGITS = "0123456789"

# اعداد حرفی به رقم
NUMBER_WORDS = {
    "صفر": "0", "یک": "1", "یه": "1", "دو": "2", "سه": "3",
    "چهار": "4", "چار": "4", "پنج": "5", "شش": "6", "شیش": "6",
    "هفت": "7", "هشت": "8", "نه": "9", "نُه": "9", "نو": "9",
    # دو رقمی‌ها
    "ده": "10", "یازده": "11", "دوازده": "12", "سیزده": "13",
    "چهارده": "14", "پانزده": "15", "شانزده": "16",
    "هفده": "17", "هجده": "18", "نوزده": "19",
    "بیست": "20", "سی": "30", "چهل": "40", "پنجاه": "50",
    "شصت": "60", "هفتاد": "70", "هشتاد": "80", "نود": "90",
    "صد": "100", "یکصد": "100", "دویست": "200", "سیصد": "300",
    "چهارصد": "400", "پانصد": "500", "ششصد": "600",
    "هفتصد": "700", "هشتصد": "800", "نهصد": "900",
    "هزار": "1000", "میلیون": "1000000", "ملیون": "1000000",
    "میلیارد": "1000000000",
}


def normalize_persian_text(text: str) -> str:
    """
    نرمال‌سازی متن خروجی Whisper:
    - تبدیل اعداد فارسی به انگلیسی
    - تبدیل اعداد حرفی به رقم
    - تمیزکاری فاصله‌ها
    """
    if not text:
        return ""

    # ۱. تبدیل اعداد فارسی به انگلیسی
    text = text.translate(str.maketrans(PERSIAN_DIGITS, ENGLISH_DIGITS))
    text = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))  # عربی

    # ۲. تبدیل اعداد حرفی به رقم (فقط وقتی کنار هم می‌آن)
    # الگو: چند کلمه‌ی عددی پشت سر هم
    words = text.split()
    result = []
    i = 0
    while i < len(words):
        w = words[i].strip("،.,؛:!?")
        if w in NUMBER_WORDS:
            # جمع کن اعداد پشت سر هم رو
            num_parts = []
            j = i
            while j < len(words):
                wj = words[j].strip("،.,؛:!?")
                if wj in NUMBER_WORDS:
                    num_parts.append(NUMBER_WORDS[wj])
                    j += 1
                else:
                    break

            # ترکیب اعداد: اگه یه عدد ساده بود، همون رو بذار
            if len(num_parts) == 1:
                result.append(num_parts[0])
            else:
                # محاسبه‌ی عدد مرکب مثل «بیست میلیون»
                total = _combine_numbers(num_parts)
                result.append(str(total))
            i = j
        else:
            result.append(words[i])
            i += 1

    text = " ".join(result)

    # ۳. تمیزکاری نهایی
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _combine_numbers(parts):
    """ترکیب اجزای عددی مثل ['20', '1000000'] = 20000000"""
    if not parts:
        return 0

    total = 0
    current = 0

    for p in parts:
        n = int(p)
        if n >= 1000:
            if current == 0:
                current = 1
            total += current * n
            current = 0
        elif n >= 100:
            if current == 0:
                current = 1
            current *= n
        else:
            current += n

    return total + current




def _normalize_phone(phone):
    """تبدیل شماره به فرمت استاندارد 09xxxxxxxxx"""
    if not phone:
        return ""
    # فقط رقم‌ها
    digits = "".join(c for c in str(phone) if c.isdigit())
    # تبدیل اعداد فارسی
    digits = digits.translate(str.maketrans(PERSIAN_DIGITS, ENGLISH_DIGITS))
    # اگه ۱۰ رقم بود و با 9 شروع می‌شد، 0 اضافه کن
    if len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    return digits






# ═══════════════════════════════════════════════════════════
# پردازش هوشمند شماره تلفن
# ═══════════════════════════════════════════════════════════

# کلمات عددی فارسی (شامل اشکال مختلف)
PHONE_DIGIT_WORDS = {
    # صفر
    "صفر": "0", "صفر ": "0",
    # یک
    "یک": "1", "یه": "1", "يک": "1", "يك": "1",
    # دو
    "دو": "2", "٢": "2",
    # سه
    "سه": "3", "سِه": "3",
    # چهار
    "چهار": "4", "چار": "4", "چهار ": "4",
    # پنج
    "پنج": "5", "پنج ": "5", "پَنج": "5",
    # شش
    "شش": "6", "شیش": "6", "شِش": "6", "شش ": "6",
    # هفت
    "هفت": "7", "هَفت": "7", "هفت ": "7",
    # هشت
    "هشت": "8", "هَشت": "8", "هشت ": "8",
    # نه
    "نه": "9", "نُه": "9", "نو": "9", "نٌه": "9",
}


def extract_phone_from_text(text: str) -> str:
    """
    استخراج شماره تلفن از متن فارسی
    - اعداد فارسی/عربی → انگلیسی
    - کلمات عددی → رقم
    - گروه‌بندی با فاصله/خط تیره → حذف
    - نرمال‌سازی نهایی: 11 رقم با 09
    
    خروجی: شماره 11 رقمی یا "" اگر پیدا نشد
    """
    if not text:
        return ""

    # ۱. تبدیل اعداد فارسی/عربی به انگلیسی
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    text = text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))

    # ۲. تبدیل کلمات عددی به رقم
    words = text.split()
    converted_words = []
    for w in words:
        # حذف علائم نگارشی
        clean = w.strip("،.,؛:!?؟")
        if clean in PHONE_DIGIT_WORDS:
            converted_words.append(PHONE_DIGIT_WORDS[clean])
        else:
            # اگه کلمه ترکیبی بود (مثلاً "صفرنه") — نادر ولی ممکنه
            converted_words.append(w)

    text = " ".join(converted_words)

    # ۳. جدا کردن دنباله‌های عددی
    # مثلاً: "یه مشتری به اسم علی با شماره 0 9 1 2 3 4 5 6 7 8 9"
    # هدف: پیدا کردن طولانی‌ترین دنباله‌ی رقم‌ها
    
    import re
    
    # همه‌ی رقم‌ها رو با فاصله جدا کن
    # بعد دنباله‌های طولانی رو پیدا کن
    
    # روش ۱: دنباله‌های رقم با فاصله (حداقل ۸ رقم)
    # مثال: "0 9 1 2 3 4 5 6 7 8 9" یا "0912345678 9"
    digits_only = re.sub(r"[^\d]", "", text)
    
    # الان digits_only همه‌ی رقم‌های متن رو داره
    # ولی ممکنه شامل شماره‌های دیگه (مثل مبلغ) هم باشه
    
    # روش دقیق‌تر: به دنبال الگوی شماره موبایل بگرد
    # الگوهای ممکن:
    # - 09123456789 (11 رقم پشت سر هم)
    # - 9123456789 (10 رقم، بدون 0)
    # - 0912345678 + 9 (11 رقم با فاصله)
    
    # پیدا کردن همه‌ی دنباله‌های رقم با طول ≥ 10
    # اول فاصله‌های اضافی رو حذف کن
    compact = re.sub(r"\s+", "", text)
    
    # الان الگوهایی مثل "09123456789" یا "0912345678" رو پیدا کن
    # دنباله‌های 10-11 رقمی که با 9 یا 0 شروع می‌شن
    patterns = [
        r"0?9\d{9}",       # 09123456789 یا 9123456789
        r"\d{11}",         # هر 11 رقمی
        r"\d{10}",         # هر 10 رقمی
    ]
    
    for pat in patterns:
        matches = re.findall(pat, compact)
        for m in matches:
            phone = _normalize_phone(m)
            if phone and len(phone) == 11:
                return phone

    # اگه هیچ الگویی پیدا نشد، سعی کن از digits_only استفاده کنی
    # ولی فقط اگه 11 رقم یا کمتر باشه
    if 10 <= len(digits_only) <= 11:
        phone = _normalize_phone(digits_only)
        if phone:
            return phone

    return ""


def _normalize_phone(phone):
    """تبدیل شماره به فرمت استاندارد 09xxxxxxxxx"""
    if not phone:
        return ""
    # فقط رقم‌ها
    digits = "".join(c for c in str(phone) if c.isdigit())
    # تبدیل اعداد فارسی
    digits = digits.translate(str.maketrans(PERSIAN_DIGITS, ENGLISH_DIGITS))
    
    # حالت ۱: 11 رقم با 09
    if len(digits) == 11 and digits.startswith("09"):
        return digits
    
    # حالت ۲: 11 رقم با 9 (بدون 0)
    if len(digits) == 11 and digits.startswith("9"):
        return "0" + digits
    
    # حالت ۳: 10 رقم با 9 → 0 اضافه کن
    if len(digits) == 10 and digits.startswith("9"):
        return "0" + digits
    
    # حالت ۴: 10 رقم با 0 → یه رقم کم داره
    if len(digits) == 10 and digits.startswith("0"):
        return digits  # ناقص ولی برمی‌گردونیم
    
    # حالت ۵: 11 رقم با هر چیزی → اگه با 9 شروع می‌شه قبوله
    if len(digits) == 11:
        return digits
    
    return ""