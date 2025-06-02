#!/bin/sh

# Exit on error
set -e

echo "Starting TinRate API entrypoint..."

# Wait for database to be ready (if using PostgreSQL)
if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for postgres..."
    
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    
    echo "PostgreSQL started"
fi

# Install/upgrade pip packages
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Static files collection failed, continuing..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create cache table
echo "Creating cache table..."
python manage.py createcachetable || echo "Cache table already exists"

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@tinrate.com').exists():
    User.objects.create_superuser(
        email='admin@tinrate.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('Superuser created: admin@tinrate.com / admin123')
else:
    print('Superuser already exists')
" || echo "Superuser creation skipped"

# Execute the command passed to docker
echo "Starting service..."
echo "Running command: $@"

# Check if command exists
if [ -z "$1" ]; then
    echo "Error: No command provided"
    exit 1
fi

# Run the command
echo "Executing command..."
exec "$@"