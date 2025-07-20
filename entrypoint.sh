#!/bin/sh
set -e

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py ingest_excel
exec gunicorn credit_approval_system.wsgi:application --bind 0.0.0.0:8000 