#!/usr/bin/env bash
set -o errexit

echo "=== BUILD.SH STARTED ==="
python --version

echo "=== INSTALLING DEPENDENCIES ==="
pip install -r requirements.txt

echo "=== COLLECTING STATIC FILES ==="
python manage.py collectstatic --noinput

echo "=== RUNNING MIGRATIONS ==="
python manage.py migrate

echo "=== SEEDING DEMO USER DATA ==="
python manage.py seed_demo_data demo_user || echo "Demo data already exists, skipping"

echo "=== BUILD.SH FINISHED ==="
