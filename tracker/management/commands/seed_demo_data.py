import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from tracker.models import Transaction, Category, Budget


User = get_user_model()


class Command(BaseCommand):
    help = "Seed realistic demo data for a specific user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User '{username}' does not exist"))
            return

        # Safety: don't duplicate
        if Transaction.objects.filter(user=user).exists():
            self.stdout.write(self.style.WARNING("User already has transactions. Seed skipped."))
            return

        today = timezone.localdate()
        month_start = today.replace(day=1)

        # Categories
        categories = [
            ("Salary", Category.Kind.INCOME),
            ("Freelance", Category.Kind.INCOME),
            ("Food", Category.Kind.EXPENSE),
            ("Transport", Category.Kind.EXPENSE),
            ("Bills", Category.Kind.EXPENSE),
            ("Subscriptions", Category.Kind.EXPENSE),
            ("Entertainment", Category.Kind.EXPENSE),
        ]

        cat_map = {}
        for name, kind in categories:
            cat, _ = Category.objects.get_or_create(user=user, name=name, kind=kind)
            cat_map[name] = cat

        # Budgets (current month)
        Budget.objects.get_or_create(
            user=user,
            category=None,
            month=month_start,
            defaults={"amount": Decimal("1500.00")}
        )
        Budget.objects.get_or_create(
            user=user,
            category=cat_map["Food"],
            month=month_start,
            defaults={"amount": Decimal("400.00")}
        )
        Budget.objects.get_or_create(
            user=user,
            category=cat_map["Transport"],
            month=month_start,
            defaults={"amount": Decimal("200.00")}
        )

        # Transactions (last 30 days)
        expense_templates = [
            ("Food", "Groceries", (8, 45)),
            ("Food", "Lunch", (10, 18)),
            ("Transport", "Bus ticket", (2, 6)),
            ("Transport", "Fuel", (25, 60)),
            ("Bills", "Electricity bill", (80, 140)),
            ("Subscriptions", "Streaming service", (8, 15)),
            ("Entertainment", "Cinema", (10, 25)),
        ]

        transactions = []

        for i in range(30):
            day = today - timedelta(days=i)

            # weekly income
            if i in (0, 7, 14, 21):
                transactions.append(Transaction(
                    user=user,
                    type=Transaction.Type.INCOME,
                    category=cat_map["Salary"],
                    amount=Decimal("500.00"),
                    description="Weekly salary",
                    date=day
                ))

            # 1–3 expenses per day
            for _ in range(random.randint(1, 3)):
                cat_name, desc, (low, high) = random.choice(expense_templates)
                amount = Decimal(str(round(random.uniform(low, high), 2)))

                transactions.append(Transaction(
                    user=user,
                    type=Transaction.Type.EXPENSE,
                    category=cat_map[cat_name],
                    amount=amount,
                    description=desc,
                    date=day
                ))

        Transaction.objects.bulk_create(transactions)

        self.stdout.write(self.style.SUCCESS(
            f"Demo data created successfully for user '{username}'"
        ))
