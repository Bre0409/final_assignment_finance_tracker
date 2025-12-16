from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from tracker.models import Transaction, Budget

def home(request):
    return render(request, "core/home.html")

@login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    tx = Transaction.objects.filter(user=request.user, date__gte=month_start, date__lte=today)
    income = tx.filter(type=Transaction.Type.INCOME).aggregate(total=Sum("amount"))["total"] or 0
    expense = tx.filter(type=Transaction.Type.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0

    budgets = Budget.objects.filter(user=request.user, month=month_start).select_related("category")
    total_budget = budgets.filter(category__isnull=True).aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "today": today,
        "month_start": month_start,
        "income": income,
        "expense": expense,
        "net": income - expense,
        "total_budget": total_budget,
    }
    return render(request, "core/dashboard.html", context)
