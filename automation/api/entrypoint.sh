#!/bin/bash
set -e

echo "=== Generating migrations for new models ==="
python manage.py makemigrations --noinput

echo "=== Applying database migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Creating superuser (if not exists) ==="
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser admin created.')
else:
    print('Superuser already exists.')
"

echo "=== Starting server ==="
if [ "$DJANGO_DEBUG" = "True" ] || [ "$DJANGO_DEBUG" = "true" ]; then
    echo "Running Django dev server on 0.0.0.0:8000"
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Running Gunicorn on 0.0.0.0:8000"
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
