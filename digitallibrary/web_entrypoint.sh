#!/bin/sh

# Wait for the database to be ready
echo "Waiting for database connection..."
while ! nc -z db 3306; do
  sleep 1
done
echo "Database is up - executing command"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn digitallibrary.wsgi:application --bind 0.0.0.0:8000
