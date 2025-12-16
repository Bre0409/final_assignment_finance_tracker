from django import forms
from django.utils import timezone
from .models import Transaction, Budget, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ("type", "category", "amount", "description", "date")
        widgets = {
            "type": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
        self.fields["description"].required = False

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ("category", "month", "amount")
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "month": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Budgets normally apply to expenses, but we allow any to keep it simple.
            self.fields["category"].queryset = Category.objects.filter(user=user)
