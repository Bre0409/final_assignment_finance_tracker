import random
from datetime import timedelta, datetime, time
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
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing demo user's transactions and budgets, then reseed.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        force = options["force"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User '{username}' does not exist"))
            return

        # If force, wipe user's data so you can reseed anytime (new month/new year)
        if force:
            Transaction.objects.filter(user=user).delete()
            Budget.objects.filter(user=user).delete()

        # don't duplicate
        if Transaction.objects.filter(user=user).exists():
            self.stdout.write(
                self.style.WARNING(
                    "User already has transactions. Seed skipped. Use --force to reseed."
                )
            )
            return

        # localdate so month is correct for your configured TIME_ZONE
        today = timezone.localdate()
        month_start = today.replace(day=1)

        
        self.stdout.write(self.style.NOTICE(f"[seed] today={today} month_start={month_start}"))

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
            defaults={"amount": Decimal("1500.00")},
        )
        Budget.objects.get_or_create(
            user=user,
            category=cat_map["Food"],
            month=month_start,
            defaults={"amount": Decimal("400.00")},
        )
        Budget.objects.get_or_create(
            user=user,
            category=cat_map["Transport"],
            month=month_start,
            defaults={"amount": Decimal("200.00")},
        )

        # Transactions (ONLY this month)
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

        # Number of days month-to-date
        days_mtd = (today - month_start).days + 1

        #  Create day-by-day FORWARD from month_start to today
        for offset in range(days_mtd):
            day = month_start + timedelta(days=offset)

            day_value = day

            # Weekly income (every 7 days from the start of the month)
            if offset % 7 == 0:
                transactions.append(
                    Transaction(
                        user=user,
                        type=Transaction.Type.INCOME,
                        category=cat_map["Salary"],
                        amount=Decimal("500.00"),
                        description="Weekly salary",
                        date=day_value,
                    )
                )

            # Small freelance income 1–2 times this month
            if random.random() < 0.08:  # ~8% chance per day
                transactions.append(
                    Transaction(
                        user=user,
                        type=Transaction.Type.INCOME,
                        category=cat_map["Freelance"],
                        amount=Decimal(str(round(random.uniform(80, 180), 2))),
                        description="Freelance payment",
                        date=day_value,
                    )
                )

            # 1–3 expenses per day
            for _ in range(random.randint(1, 3)):
                cat_name, desc, (low, high) = random.choice(expense_templates)
                amount = Decimal(str(round(random.uniform(low, high), 2)))

                transactions.append(
                    Transaction(
                        user=user,
                        type=Transaction.Type.EXPENSE,
                        category=cat_map[cat_name],
                        amount=amount,
                        description=desc,
                        date=day_value,
                    )
                )

        Transaction.objects.bulk_create(transactions)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data created successfully for user '{username}' for {month_start} → {today}"
            )
        )
