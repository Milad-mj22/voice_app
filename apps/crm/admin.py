from django.contrib import admin
from .models import (
    Customer, Project, Opportunity, Task,
    Finance, Supplier, Colleague, Competitor, Strategy,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("title", "phone", "company", "status", "business", "created_at")
    list_filter = ("status", "business")
    search_fields = ("title", "phone", "company", "notes")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "status", "progress", "budget", "business")
    list_filter = ("status", "business")
    search_fields = ("title", "customer__title", "notes")


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "stage", "amount", "probability", "business")
    list_filter = ("stage", "business")
    search_fields = ("title", "customer__title")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "assignee", "priority", "due_date", "is_done", "business")
    list_filter = ("priority", "is_done", "business")
    search_fields = ("title", "notes")


@admin.register(Finance)
class FinanceAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "amount", "category", "business", "date")
    list_filter = ("type", "category", "business")
    search_fields = ("title", "notes")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("title", "phone", "contact_person", "business")
    search_fields = ("title", "phone", "products")


@admin.register(Colleague)
class ColleagueAdmin(admin.ModelAdmin):
    list_display = ("title", "position", "phone", "business")
    list_filter = ("position", "business")
    search_fields = ("title", "phone", "responsibilities")


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = ("title", "phone", "website", "business")
    search_fields = ("title", "notes")


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "created_at")
    search_fields = ("title", "mission", "vision", "goals")