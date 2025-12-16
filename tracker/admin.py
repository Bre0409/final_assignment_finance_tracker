from django.contrib import admin
from .models import Category, Transaction, Budget

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "user")
    list_filter = ("kind",)
    search_fields = ("name", "user__username")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "type", "amount", "category", "user")
    list_filter = ("type", "date")
    search_fields = ("description", "category__name", "user__username")

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("month", "category", "amount", "user")
    list_filter = ("month",)
