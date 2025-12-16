from django.conf import settings
from django.db import models
from django.utils import timezone

class Category(models.Model):
    class Kind(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.EXPENSE)

    class Meta:
        unique_together = ("user", "name", "kind")
        ordering = ["kind", "name"]

    def __str__(self):
        return f"{self.name} ({self.kind})"

class Transaction(models.Model):
    class Type(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.EXPENSE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    date = models.DateField(default=timezone.localdate)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.type}: {self.amount} on {self.date}"

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    # category null = "overall monthly budget"
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="budgets")
    month = models.DateField(help_text="Use the first day of the month (e.g., 2025-12-01).")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "category", "month")
        ordering = ["-month", "category__name"]

    def __str__(self):
        label = self.category.name if self.category else "Overall"
        return f"{label} - {self.month}: {self.amount}"
