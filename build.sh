#!/usr/bin/env bash
set -o errexit

echo "=== BUILD.SH STARTED ==="
python --version
pwd
ls -la

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

echo "=== RUNNING CREATE_SUPERUSER ==="
python create_superuser.py
echo "=== CREATE_SUPERUSER FINISHED ==="

echo "=== BUILD.SH FINISHED ==="
