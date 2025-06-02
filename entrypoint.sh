#!/bin/sh

# Exit on error
set -e

# Install netcat for service checking
apt-get update && apt-get install -y netcat-openbsd

# Ensure gunicorn is installed
if ! command -v gunicorn > /dev/null 2>&1; then
    echo "Installing gunicorn..."
    pip install gunicorn
files
# Create cache table
echo "Creating cache table..."
python manage.py createcachetable

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