from django.db import models
from django.conf import settings


class BaseRecord(models.Model):
    """
    کلاس انتزاعی مشترک برای همه‌ی رکوردهای CRM
    هر رکورد به یک کسب‌وکار تعلق داره
    """
    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="%(class)s_records",
        verbose_name="کسب‌وکار",
    )
    title = models.CharField("عنوان / نام", max_length=200)
    status = models.CharField("وضعیت", max_length=50, default="جدید")
    date = models.DateField("تاریخ", null=True, blank=True)
    notes = models.TextField("یادداشت", blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_created",
        verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Customer(BaseRecord):
    """مشتری / ارتباط"""
    phone = models.CharField("شماره تماس", max_length=20, blank=True)
    company = models.CharField("شرکت", max_length=150, blank=True)
    email = models.EmailField("ایمیل", blank=True)
    address = models.TextField("آدرس", blank=True)

    # فیلدهای مخصوص فروش
    source = models.CharField("منبع آشنایی", max_length=100, blank=True)
    tags = models.CharField("برچسب‌ها", max_length=200, blank=True,
                            help_text="با کاما جدا کن")

    class Meta(BaseRecord.Meta):
        verbose_name = "مشتری"
        verbose_name_plural = "مشتریان"


class Project(BaseRecord):
    """پروژه"""
    STATUS_CHOICES = [
        ("جدید", "جدید"),
        ("در حال پیگیری", "در حال پیگیری"),
        ("فعال", "فعال"),
        ("انجام شد", "انجام شد"),
        ("لغو شد", "لغو شد"),
        ("بایگانی", "بایگانی"),
    ]
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="projects",
        verbose_name="مشتری",
    )
    start_date = models.DateField("تاریخ شروع", null=True, blank=True)
    end_date = models.DateField("تاریخ پایان", null=True, blank=True)
    budget = models.DecimalField("بودجه (تومان)", max_digits=15,
                                 decimal_places=0, null=True, blank=True)
    progress = models.PositiveIntegerField("درصد پیشرفت", default=0)

    class Meta(BaseRecord.Meta):
        verbose_name = "پروژه"
        verbose_name_plural = "پروژه‌ها"


class Opportunity(BaseRecord):
    """فرصت فروش"""
    STAGE_CHOICES = [
        ("سرنخ", "سرنخ"),
        ("تماس اولیه", "تماس اولیه"),
        ("نیازسنجی", "نیازسنجی"),
        ("ارائه پیشنهاد", "ارائه پیشنهاد"),
        ("مذاکره", "مذاکره"),
        ("برنده", "برنده"),
        ("باخت", "باخت"),
    ]
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="opportunities",
        verbose_name="مشتری",
    )
    amount = models.DecimalField("مبلغ (تومان)", max_digits=15,
                                 decimal_places=0, null=True, blank=True)
    stage = models.CharField("مرحله فروش", max_length=50,
                             choices=STAGE_CHOICES, default="سرنخ")
    probability = models.PositiveIntegerField("احتمال موفقیت (%)", default=50)
    expected_close = models.DateField("تاریخ بستن احتمالی", null=True, blank=True)

    class Meta(BaseRecord.Meta):
        verbose_name = "فرصت فروش"
        verbose_name_plural = "فرصت‌های فروش"


class Task(BaseRecord):
    """پیگیری / وظیفه"""
    PRIORITY_CHOICES = [
        ("کم", "کم"),
        ("متوسط", "متوسط"),
        ("زیاد", "زیاد"),
        ("فوری", "فوری"),
    ]
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="tasks",
        verbose_name="مسئول",
    )
    due_date = models.DateField("مهلت انجام", null=True, blank=True)
    priority = models.CharField("اولویت", max_length=20,
                                choices=PRIORITY_CHOICES, default="متوسط")
    is_done = models.BooleanField("انجام شد", default=False)

    class Meta(BaseRecord.Meta):
        verbose_name = "پیگیری"
        verbose_name_plural = "پیگیری‌ها"


class Finance(BaseRecord):
    """تراکنش مالی"""
    TYPE_CHOICES = [
        ("درآمد", "درآمد"),
        ("هزینه", "هزینه"),
    ]
    type = models.CharField("نوع", max_length=20, choices=TYPE_CHOICES,
                            default="درآمد")
    amount = models.DecimalField("مبلغ (تومان)", max_digits=15,
                                 decimal_places=0, default=0)
    category = models.CharField("دسته", max_length=100, blank=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions",
        verbose_name="مشتری مرتبط",
    )
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions",
        verbose_name="پروژه مرتبط",
    )

    class Meta(BaseRecord.Meta):
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"


class Supplier(BaseRecord):
    """تأمین‌کننده"""
    phone = models.CharField("شماره تماس", max_length=20, blank=True)
    contact_person = models.CharField("شخص رابط", max_length=100, blank=True)
    products = models.TextField("کالاها/خدمات", blank=True)
    payment_terms = models.CharField("شرایط پرداخت", max_length=200, blank=True)

    class Meta(BaseRecord.Meta):
        verbose_name = "تأمین‌کننده"
        verbose_name_plural = "تأمین‌کنندگان"


class Colleague(BaseRecord):
    """همکار"""
    ROLE_CHOICES = [
        ("مدیر", "مدیر"),
        ("فروش", "فروش"),
        ("فنی", "فنی"),
        ("مالی", "مالی"),
        ("پشتیبانی", "پشتیبانی"),
        ("سایر", "سایر"),
    ]
    phone = models.CharField("شماره تماس", max_length=20, blank=True)
    position = models.CharField("سمت", max_length=100,
                                choices=ROLE_CHOICES, blank=True)
    responsibilities = models.TextField("مسئولیت‌ها", blank=True)
    user_account = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="colleague_profile",
        verbose_name="حساب کاربری",
    )

    class Meta(BaseRecord.Meta):
        verbose_name = "همکار"
        verbose_name_plural = "همکاران"


class Competitor(BaseRecord):
    """رقیب"""
    phone = models.CharField("شماره تماس", max_length=20, blank=True)
    website = models.URLField("وب‌سایت", blank=True)
    strengths = models.TextField("نقاط قوت", blank=True)
    weaknesses = models.TextField("نقاط ضعف", blank=True)

    class Meta(BaseRecord.Meta):
        verbose_name = "رقیب"
        verbose_name_plural = "رقبا"


class Strategy(BaseRecord):
    """استراتژی"""
    mission = models.TextField("ماموریت", blank=True)
    vision = models.TextField("چشم‌انداز", blank=True)
    goals = models.TextField("اهداف", blank=True)
    kpis = models.TextField("شاخص‌های کلیدی (KPI)", blank=True)

    class Meta(BaseRecord.Meta):
        verbose_name = "استراتژی"
        verbose_name_plural = "استراتژی‌ها"