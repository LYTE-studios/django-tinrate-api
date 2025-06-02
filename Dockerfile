FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        netcat-openbsd \
        curl \
        git \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
        gunicorn \
        whitenoise

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy project files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "tinrate_api.wsgi:application"]