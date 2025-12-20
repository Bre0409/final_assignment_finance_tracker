from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from tracker.models import Transaction, Budget
from services.currency import get_latest_rates, convert


def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    tx = Transaction.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=today
    )

    income = tx.filter(type=Transaction.Type.INCOME).aggregate(total=Sum("amount"))["total"] or 0
    expense = tx.filter(type=Transaction.Type.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0

    budgets = Budget.objects.filter(user=request.user, month=month_start).select_related("category")
    total_budget = budgets.filter(category__isnull=True).aggregate(total=Sum("amount"))["total"] or 0

    # -----------------------------
    # Currency display selection
    # -----------------------------
    allowed = ("EUR", "USD", "GBP")

    selected = request.GET.get("currency")
    if selected in allowed:
        request.session["display_currency"] = selected

    display_currency = request.session.get("display_currency", "EUR")
    if display_currency not in allowed:
        display_currency = "EUR"

    symbol_map = {"EUR": "€", "USD": "$", "GBP": "£"}

    # -----------------------------
    # FX (API) - always fetch from EUR (base data currency)
    # -----------------------------
    fx = None
    fx_error = None
    fx_date = None

    try:
        # We store amounts in EUR, so we fetch EUR -> USD/GBP once
        fx = get_latest_rates(base="EUR", symbols=("USD", "GBP"))
        fx_date = fx.date
    except Exception:
        fx_error = "Rates unavailable right now."

    # Determine the rate needed for selected display currency
    rate = None
    if display_currency == "EUR":
        rate = None
    elif fx:
        rate = fx.rates.get(display_currency)

    # Display totals in selected currency
    display_income = convert(income, rate) if rate else income
    display_expense = convert(expense, rate) if rate else expense
    display_net = convert(income - expense, rate) if rate else (income - expense)

    context = {
        "today": today,
        "month_start": month_start,

        # Raw EUR totals (still useful)
        "income": income,
        "expense": expense,
        "net": income - expense,

        # Budgets
        "total_budget": total_budget,

        # Currency display
        "display_currency": display_currency,
        "display_symbol": symbol_map.get(display_currency, "€"),
        "display_income": display_income,
        "display_expense": display_expense,
        "display_net": display_net,

        # FX info + errors
        "fx": fx,
        "fx_date": fx_date,
        "fx_error": fx_error,
    }

    return render(request, "core/dashboard.html", context)
