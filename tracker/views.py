from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import TransactionForm, BudgetForm
from .models import Transaction, Budget, Category


class UserQuerySetMixin(LoginRequiredMixin):
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "tracker/transactions/list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related("category")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)
        tx = self.get_queryset().filter(date__gte=month_start, date__lte=today)
        ctx["income"] = tx.filter(type=Transaction.Type.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        ctx["expense"] = tx.filter(type=Transaction.Type.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        ctx["month_start"] = month_start
        ctx["today"] = today
        return ctx


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = "tracker/transactions/form.html"
    success_url = reverse_lazy("transaction_list")

    def get_form_class(self):
        return TransactionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        messages.success(self.request, "Transaction added.")
        return redirect(self.success_url)


class TransactionUpdateView(UserQuerySetMixin, UpdateView):
    model = Transaction
    template_name = "tracker/transactions/form.html"
    success_url = reverse_lazy("transaction_list")

    def get_form_class(self):
        return TransactionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Transaction updated.")
        return super().form_valid(form)


class TransactionDeleteView(UserQuerySetMixin, DeleteView):
    model = Transaction
    template_name = "tracker/transactions/confirm_delete.html"
    success_url = reverse_lazy("transaction_list")

    def delete(self, request, *args, **kwargs):
        messages.info(self.request, "Transaction deleted.")
        return super().delete(request, *args, **kwargs)


def budget_overview(request):
    if not request.user.is_authenticated:
        return redirect("login")

    today = timezone.localdate()
    month_start = today.replace(day=1)

    # Basic categories seed (optional): create a few defaults if user has none
    if not Category.objects.filter(user=request.user).exists():
        Category.objects.bulk_create([
            Category(user=request.user, name="Salary", kind=Category.Kind.INCOME),
            Category(user=request.user, name="Food", kind=Category.Kind.EXPENSE),
            Category(user=request.user, name="Transport", kind=Category.Kind.EXPENSE),
            Category(user=request.user, name="Bills", kind=Category.Kind.EXPENSE),
        ])

    if request.method == "POST":
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            # normalize month to first of month
            budget.month = budget.month.replace(day=1)
            budget.save()
            messages.success(request, "Budget saved.")
            return redirect("budget_overview")
    else:
        form = BudgetForm(initial={"month": month_start}, user=request.user)

    budgets = Budget.objects.filter(user=request.user, month=month_start).select_related("category")

    # month-to-date spending per category (expenses only)
    spending = (
        Transaction.objects.filter(user=request.user, type=Transaction.Type.EXPENSE, date__gte=month_start, date__lte=today)
        .values("category__id", "category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    context = {
        "form": form,
        "budgets": budgets,
        "month_start": month_start,
        "today": today,
        "spending": spending,
    }
    return render(request, "tracker/budgets/overview.html", context)
