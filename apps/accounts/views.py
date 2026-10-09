from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .models import Business, User
from .forms import BusinessForm, RegisterForm, UserForm, ProfileForm


# ============================================================
# احراز هویت
# ============================================================

def register_view(request):
    """ثبت‌نام کسب‌وکار جدید + ساخت Owner"""
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # ساخت Business
            biz_name = form.cleaned_data["business_name"]
            base_slug = slugify(biz_name, allow_unicode=True) or f"biz-{user.id}"
            slug = base_slug
            i = 2
            while Business.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1

            business = Business.objects.create(
                name=biz_name,
                slug=slug,
                phone=form.cleaned_data["phone"],
            )
            user.business = business
            user.save()

            login(request, user)
            messages.success(request, "خوش آمدید! کسب‌وکار شما ساخته شد.")
            return redirect("/")
        else:
            messages.error(request, "لطفاً خطاهای فرم را برطرف کنید.")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")


# ============================================================
# تنظیمات کسب‌وکار
# ============================================================

@login_required
def settings_view(request):
    """تنظیمات کسب‌وکار (فقط Owner/Admin)"""
    business = getattr(request, "business", None) or request.user.business
    if not business:
        return redirect("/accounts/register/")

    if request.user.role not in ("owner", "admin"):
        messages.error(request, "شما دسترسی به این بخش ندارید.")
        return redirect("/")

    if request.method == "POST":
        form = BusinessForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات ذخیره شد.")
            return redirect("accounts_settings")
    else:
        form = BusinessForm(instance=business)

    return render(request, "accounts/settings.html", {
        "form": form,
        "business": business,
    })


# ============================================================
# مدیریت کاربران
# ============================================================

@login_required
def users_view(request):
    """لیست کاربران کسب‌وکار"""
    business = getattr(request, "business", None) or request.user.business
    if not business:
        return redirect("/")

    if request.user.role not in ("owner", "admin"):
        messages.error(request, "دسترسی ندارید.")
        return redirect("/")

    users = User.objects.filter(business=business).order_by("-date_joined")
    return render(request, "accounts/users.html", {
        "users": users,
        "business": business,
    })


@login_required
def user_create_view(request):
    """افزودن کاربر جدید"""
    business = getattr(request, "business", None) or request.user.business
    if not business or request.user.role not in ("owner", "admin"):
        return redirect("/")

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data.get("password"):
                messages.error(request, "برای کاربر جدید رمز عبور الزامی است.")
            else:
                form.save(business=business)
                messages.success(request, "کاربر اضافه شد.")
                return redirect("accounts_users")
    else:
        form = UserForm()

    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": "افزودن کاربر",
    })


@login_required
def user_edit_view(request, pk):
    """ویرایش کاربر"""
    business = getattr(request, "business", None) or request.user.business
    if not business or request.user.role not in ("owner", "admin"):
        return redirect("/")

    user_obj = get_object_or_404(User, pk=pk, business=business)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save(business=business)
            messages.success(request, "کاربر ویرایش شد.")
            return redirect("accounts_users")
    else:
        form = UserForm(instance=user_obj)

    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": "ویرایش کاربر",
        "edit_user": user_obj,
    })


@login_required
@require_POST
def user_delete_view(request, pk):
    """حذف کاربر"""
    business = getattr(request, "business", None) or request.user.business
    if not business or request.user.role not in ("owner", "admin"):
        return JsonResponse({"error": "دسترسی ندارید."}, status=403)

    user_obj = get_object_or_404(User, pk=pk, business=business)

    if user_obj == request.user:
        return JsonResponse({"error": "نمی‌تونی خودت رو حذف کنی."}, status=400)

    if user_obj.role == "owner":
        return JsonResponse({"error": "مالک قابل حذف نیست."}, status=400)

    user_obj.delete()
    return JsonResponse({"ok": True})


# ============================================================
# پروفایل خودم
# ============================================================

@login_required
def profile_view(request):
    """ویرایش پروفایل + تغییر رمز"""
    profile_form = ProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "پروفایل ذخیره شد.")
                return redirect("accounts_profile")

        elif action == "password":
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "رمز عبور تغییر کرد.")
                return redirect("accounts_profile")

    return render(request, "accounts/profile.html", {
        "profile_form": profile_form,
        "password_form": password_form,
    })


# ============================================================
# API: آپلود لوگو (Ajax)
# ============================================================

@login_required
@require_POST
def upload_logo_view(request):
    """آپلود سریع لوگو با Ajax"""
    business = getattr(request, "business", None) or request.user.business
    if not business or request.user.role not in ("owner", "admin"):
        return JsonResponse({"error": "دسترسی ندارید."}, status=403)

    logo = request.FILES.get("logo")
    if not logo:
        return JsonResponse({"error": "فایلی انتخاب نشده."}, status=400)

    if logo.size > 2 * 1024 * 1024:
        return JsonResponse({"error": "حجم لوگو باید کمتر از ۲ مگابایت باشد."}, status=400)

    business.logo = logo
    business.save()
    return JsonResponse({"ok": True, "url": business.logo.url})