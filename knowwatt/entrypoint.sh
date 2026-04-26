#!/bin/bash

# Wait for database
if [ "$DEBUG" = "False" ]; then
    echo "Waiting for postgres..."
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start services based on command
exec "$@"
