import calendar
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from tracker.models import Transaction, Budget
from services.currency import get_latest_rates, convert


def _build_trend_series(user, display_rate=None, days=30):
    """
    Returns (days, labels, series) for daily expense totals.
    Values are stored in EUR; if display_rate is provided, values are converted for display.
    """
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)

    daily_qs = (
        Transaction.objects
        .filter(
            user=user,
            type=Transaction.Type.EXPENSE,
            date__gte=start_date,
            date__lte=today
        )
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )

    totals_by_day = {row["date"]: row["total"] for row in daily_qs}

    labels = []
    series = []

    for i in range(days):
        d = start_date + timedelta(days=i)
        total_eur = totals_by_day.get(d, 0) or 0

        labels.append(d.strftime("%d %b"))
        if display_rate:
            series.append(float(convert(total_eur, display_rate)))
        else:
            series.append(float(total_eur))

    return days, labels, series


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
    # Currency selection (display only)
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
    # FX rates (base EUR)
    # -----------------------------
    fx = None
    fx_error = None
    fx_date = None

    try:
        fx = get_latest_rates(base="EUR", symbols=("USD", "GBP"))
        fx_date = fx.date
    except Exception:
        fx_error = "Rates unavailable right now."

    rate = None
    if display_currency != "EUR" and fx:
        rate = fx.rates.get(display_currency)

    # Converted totals (for display)
    display_income = convert(income, rate) if rate else income
    display_expense = convert(expense, rate) if rate else expense
    display_net = convert(income - expense, rate) if rate else (income - expense)

    # -----------------------------
    # Line trend chart data (last 30 days)
    # -----------------------------
    trend_days, trend_labels, trend_series = _build_trend_series(
        request.user,
        display_rate=rate,
        days=30
    )

    # -----------------------------
    # Budget limit line (monthly overall budget -> daily limit)
    # -----------------------------
    days_in_month = calendar.monthrange(month_start.year, month_start.month)[1]

    daily_budget_limit_eur = None
    if total_budget and total_budget > 0 and days_in_month:
        daily_budget_limit_eur = float(total_budget) / float(days_in_month)

    daily_budget_limit_display = None
    if daily_budget_limit_eur is not None:
        daily_budget_limit_display = float(convert(daily_budget_limit_eur, rate)) if rate else daily_budget_limit_eur

    trend_budget_line = None
    if daily_budget_limit_display is not None:
        trend_budget_line = [float(daily_budget_limit_display)] * len(trend_labels)

    # -----------------------------
    # Doughnut chart: spending by category (month-to-date)
    # + breakdown table: amount + percent
    # -----------------------------
    spend_rows = (
        Transaction.objects.filter(
            user=request.user,
            type=Transaction.Type.EXPENSE,
            date__gte=month_start,
            date__lte=today
        )
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    total_spend_eur = sum((r["total"] or 0) for r in spend_rows) or 0

    spend_pie_labels = []
    spend_pie_series = []
    spend_breakdown = []

    for r in spend_rows:
        name = r["category__name"] or "Uncategorised"
        total_eur = r["total"] or 0

        amount_display = float(convert(total_eur, rate)) if rate else float(total_eur)

        spend_pie_labels.append(name)
        spend_pie_series.append(amount_display)

        pct = 0
        if total_spend_eur:
            pct = round((float(total_eur) / float(total_spend_eur)) * 100)

        spend_breakdown.append({
            "name": name,
            "amount": f"{amount_display:,.2f}",
            "percent": pct,
        })

    # -----------------------------
    # Budget insights (EUR-based for correctness)
    # -----------------------------
    insights = []
    insight_level = "secondary"

    if total_budget and total_budget > 0:
        remaining = total_budget - expense
        pct_used = float((expense / total_budget) * 100) if total_budget else 0.0

        if remaining < 0:
            insight_level = "danger"
            insights.append(f"You are over your overall budget by €{abs(remaining):.2f} this month.")
        elif pct_used >= 90:
            insight_level = "warning"
            insights.append(f"You have used {pct_used:.0f}% of your overall budget. Remaining: €{remaining:.2f}.")
        else:
            insight_level = "success"
            insights.append(f"You have used {pct_used:.0f}% of your overall budget. Remaining: €{remaining:.2f}.")
    else:
        insights.append("No overall budget set for this month yet. Add one in Budgets to track progress.")

    category_budgets = budgets.exclude(category__isnull=True)
    if category_budgets.exists():
        spend_rows2 = (
            Transaction.objects.filter(
                user=request.user,
                type=Transaction.Type.EXPENSE,
                date__gte=month_start,
                date__lte=today,
                category__isnull=False
            )
            .values("category_id", "category__name")
            .annotate(total=Sum("amount"))
        )
        spend_map = {r["category_id"]: (r["category__name"], r["total"] or 0) for r in spend_rows2}

        best = None  # (pct_used, name, spent, budget_amount)
        for b in category_budgets:
            spent_name, spent = spend_map.get(b.category_id, (b.category.name, 0))
            if b.amount and b.amount > 0:
                pct = float((spent / b.amount) * 100)
                candidate = (pct, spent_name, spent, b.amount)
                if (best is None) or (candidate[0] > best[0]):
                    best = candidate

        if best:
            pct, name, spent, budget_amt = best
            if pct >= 100:
                insights.append(f"⚠ {name} is over budget: €{spent:.2f} / €{budget_amt:.2f} ({pct:.0f}%).")
            elif pct >= 80:
                insights.append(f"{name} is close to budget: €{spent:.2f} / €{budget_amt:.2f} ({pct:.0f}%).")
            else:
                insights.append(f"Top category usage: {name} €{spent:.2f} / €{budget_amt:.2f} ({pct:.0f}%).")

    context = {
        "today": today,
        "month_start": month_start,

        # Raw EUR totals
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

        # FX
        "fx": fx,
        "fx_date": fx_date,
        "fx_error": fx_error,

        # Trend charts
        "trend_days": trend_days,
        "trend_labels": trend_labels,
        "trend_series": trend_series,

        # Budget limit (daily) for charts
        "daily_budget_limit": daily_budget_limit_display,
        "trend_budget_line": trend_budget_line,

        # Doughnut + metrics
        "spend_pie_labels": spend_pie_labels,
        "spend_pie_series": spend_pie_series,
        "spend_breakdown": spend_breakdown,

        # Insights
        "budget_insights": insights,
        "insight_level": insight_level,
    }

    return render(request, "core/dashboard.html", context)
