from django.urls import path
from . import api

urlpatterns = [
    path("api/stats/", api.stats_view, name="api_stats"),
    path("api/search/", api.search_view, name="api_search"),
    path("api/export/", api.export_view, name="api_export"),

    # گزارش‌ها
    path("api/reports/pipeline/", api.report_pipeline_view, name="api_report_pipeline"),
    path("api/reports/monthly/", api.report_monthly_view, name="api_report_monthly"),
    path("api/reports/weekly/", api.report_weekly_view, name="api_report_weekly"),
    path("api/reports/top-customers/", api.report_top_customers_view, name="api_report_top_customers"),

    # CRUD
    path("api/<str:record_type>/", api.records_view, name="api_records"),
    path("api/<str:record_type>/<int:pk>/", api.record_detail_view, name="api_record_detail"),
]