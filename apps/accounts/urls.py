from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ورود / خروج
    path("login/", auth_views.LoginView.as_view(
        template_name="accounts/login.html"
    ), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # تنظیمات کسب‌وکار
    path("settings/", views.settings_view, name="accounts_settings"),

    # مدیریت کاربران
    path("users/", views.users_view, name="accounts_users"),
    path("users/new/", views.user_create_view, name="accounts_user_create"),
    path("users/<int:pk>/edit/", views.user_edit_view, name="accounts_user_edit"),
    path("users/<int:pk>/delete/", views.user_delete_view, name="accounts_user_delete"),

    # پروفایل
    path("profile/", views.profile_view, name="accounts_profile"),

    # API
    path("api/upload-logo/", views.upload_logo_view, name="accounts_upload_logo"),
]