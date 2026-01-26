import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finance_tracker.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ["ADMIN_USERNAME"]
email = os.environ["ADMIN_EMAIL"]
password = os.environ["ADMIN_PASSWORD"]

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser created")
else:
    print("Superuser already exists")
