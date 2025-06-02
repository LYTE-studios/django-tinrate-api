# Docker Deployment Guide for TinRate API

## 🐳 Docker Setup

This guide will help you deploy the TinRate API using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM available
- Port 80 and 5432 available

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd django-tinrate-api
```

### 2. Configure Environment

The Docker setup uses `.env` for configuration. Update it as needed:

```bash
cp .env .env.local
# Edit .env.local with your specific settings
```

### 3. Build and Run

```bash
# Build and start all services
docker-compose up --build -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Access the API

- **API**: http://localhost (or your domain)
- **Health Check**: http://localhost/v1/health/
- **Admin**: http://localhost/admin/ (admin@tinrate.com / admin123)

## 🏗️ Architecture

The Docker setup includes:

- **web**: Django application with Gunicorn
- **db**: PostgreSQL 15 database
- **nginx**: Reverse proxy and static file server

## 📁 Docker Files

### Dockerfile
- Based on Python 3.11 slim
- Installs system dependencies
- Sets up Python environment
- Configures entrypoint

### docker-compose.yaml
- Multi-service setup
- PostgreSQL database
- Nginx reverse proxy
- Volume management
- Health checks

### entrypoint.sh
- Database migration
- Static file collection
- Cache table creation
- Superuser creation

## 🔧 Configuration

### Environment Variables (.env)

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,your-domain.com

# Database
DATABASE=postgres
DB_NAME=tinrate_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# AWS S3 (optional)
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=eu-central-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Nginx Configuration

The nginx.conf handles:
- Static file serving
- Media file serving
- Proxy to Django app
- Security headers
- Gzip compression

## 🛠️ Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

### Execute Commands in Container
```bash
# Django shell
docker-compose exec web python manage.py shell

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic
```

### Database Management
```bash
# Access PostgreSQL
docker-compose exec db psql -U postgres -d tinrate_db

# Backup database
docker-compose exec db pg_dump -U postgres tinrate_db > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres tinrate_db < backup.sql
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 80
   sudo lsof -i :80
   
   # Change port in docker-compose.yaml
   ports:
     - "8080:80"  # Use port 8080 instead
   ```

2. **Permission Denied on entrypoint.sh**
   ```bash
   # Make sure entrypoint.sh is executable
   chmod +x entrypoint.sh
   
   # Rebuild container
   docker-compose build --no-cache web
   ```

3. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Restart database
   docker-compose restart db
   ```

4. **Static Files Not Loading**
   ```bash
   # Collect static files
   docker-compose exec web python manage.py collectstatic --noinput
   
   # Check nginx logs
   docker-compose logs nginx
   ```

### Health Checks

```bash
# API Health
curl http://localhost/v1/health/

# Database Health
docker-compose exec db pg_isready -U postgres

# Container Status
docker-compose ps
```

## 🔒 Security Considerations

### Production Deployment

1. **Change Default Passwords**
   ```env
   DB_PASSWORD=your-secure-password
   SECRET_KEY=your-secure-secret-key
   ```

2. **Use HTTPS**
   - Configure SSL certificates
   - Update nginx.conf for HTTPS
   - Set SECURE_SSL_REDIRECT=True

3. **Environment Variables**
   - Never commit .env files
   - Use Docker secrets for sensitive data
   - Rotate keys regularly

4. **Database Security**
   - Use strong passwords
   - Limit database access
   - Regular backups

## 📊 Monitoring

### Container Monitoring
```bash
# Resource usage
docker stats

# Container health
docker-compose ps

# Service logs
docker-compose logs --tail=100 -f
```

### Application Monitoring
- Health check endpoint: `/v1/health/`
- Admin interface: `/admin/`
- API documentation: Available in README.md

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Run migrations if needed
docker-compose exec web python manage.py migrate
```

### Backup Strategy
```bash
# Database backup
docker-compose exec db pg_dump -U postgres tinrate_db > backup_$(date +%Y%m%d).sql

# Volume backup
docker run --rm -v django-tinrate-api_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_backup.tar.gz /data
```

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify configuration: Review .env
3. Test connectivity: Use health check endpoints
4. Restart services: `docker-compose restart`

For additional help, refer to the main README.md or create an issue in the repository.