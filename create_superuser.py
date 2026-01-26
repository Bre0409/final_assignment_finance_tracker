import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finance_tracker.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("ADMIN_USERNAME", "admin")
email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
password = os.environ.get("ADMIN_PASSWORD")

if not password:
    raise SystemExit("ADMIN_PASSWORD is not set. Add it in render.yaml envVars temporarily.")

user, created = User.objects.get_or_create(username=username, defaults={"email": email})

# ALWAYS enforce admin flags + reset password (temporary but guarantees access)
user.email = email
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

print("Superuser created and/or password reset successfully.")
