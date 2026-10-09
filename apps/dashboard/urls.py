from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="dashboard_home"),
    path("reports/", views.reports, name="dashboard_reports"),
]