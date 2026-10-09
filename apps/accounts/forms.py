from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Business, User


class BusinessForm(forms.ModelForm):
    """فرم تنظیمات کسب‌وکار"""
    class Meta:
        model = Business
        fields = ["name", "slug", "logo", "brand_color", "phone", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "slug": forms.TextInput(attrs={"class": "form-input", "dir": "ltr"}),
            "brand_color": forms.TextInput(attrs={"type": "color", "class": "form-color"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "dir": "ltr"}),
            "address": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }


class RegisterForm(UserCreationForm):
    """فرم ثبت‌نام کسب‌وکار جدید"""
    business_name = forms.CharField(
        label="نام کسب‌وکار",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "مثلاً برق مرداس"}),
    )
    phone = forms.CharField(
        label="شماره موبایل",
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-input", "dir": "ltr", "placeholder": "09123456789"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-input").strip()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone = self.cleaned_data["phone"]
        user.role = "owner"
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    """فرم افزودن/ویرایش کاربر توسط مالک"""
    password = forms.CharField(
        label="رمز عبور",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
        help_text="برای کاربر جدید الزامی است. برای ویرایش، خالی بگذارید.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "role"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "dir": "ltr"}),
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "dir": "ltr"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "dir": "ltr"}),
            "role": forms.Select(attrs={"class": "form-input"}),
        }

    def save(self, commit=True, business=None):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if business:
            user.business = business
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """فرم پروفایل خود کاربر"""
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "dir": "ltr"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "dir": "ltr"}),
        }