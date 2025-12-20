from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Transaction, Budget, Category


class TrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="StrongPass12345!")
        self.client.login(username="u1", password="StrongPass12345!")

        # Create categories for the user
        self.income_cat = Category.objects.create(
            user=self.user, name="Salary", kind=Category.Kind.INCOME
        )
        self.expense_cat = Category.objects.create(
            user=self.user, name="Food", kind=Category.Kind.EXPENSE
        )

    def test_create_transaction(self):
        url = reverse("transaction_create")
        resp = self.client.post(url, {
            "type": Transaction.Type.EXPENSE,
            "category": self.expense_cat.id,
            "amount": "12.50",
            "description": "Lunch",
            "date": str(timezone.localdate()),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 1)

        t = Transaction.objects.get(user=self.user)
        self.assertEqual(t.amount, Decimal("12.50"))
        self.assertEqual(t.description, "Lunch")

    def test_transaction_list_loads(self):
        Transaction.objects.create(
            user=self.user,
            type=Transaction.Type.INCOME,
            category=self.income_cat,
            amount=Decimal("100.00"),
            description="Pay",
            date=timezone.localdate(),
        )
        resp = self.client.get(reverse("transaction_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Transactions")

    def test_budget_create(self):
        url = reverse("budget_overview")
        month_start = timezone.localdate().replace(day=1)

        resp = self.client.post(url, {
            "category": "",  # overall budget
            "month": str(month_start),
            "amount": "300.00",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Budget.objects.filter(user=self.user).count(), 1)

        b = Budget.objects.get(user=self.user)
        self.assertEqual(b.amount, Decimal("300.00"))
        self.assertEqual(b.month.day, 1)
        self.assertIsNone(b.category)

    def test_transaction_pages_require_login(self):
        self.client.logout()
        resp = self.client.get(reverse("transaction_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)
