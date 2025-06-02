#!/bin/bash

echo "🐳 Testing Docker Deployment for TinRate API"
echo "============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

echo "✅ docker-compose is available"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if containers are running
echo "🔍 Checking container status..."
docker-compose ps

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost/v1/health/ > /dev/null 2>&1; then
    echo "✅ Health endpoint is working"
else
    echo "❌ Health endpoint failed"
    echo "📋 Container logs:"
    docker-compose logs --tail=20
    exit 1
fi

# Test config endpoint
echo "⚙️  Testing config endpoint..."
if curl -f http://localhost/v1/config/ > /dev/null 2>&1; then
    echo "✅ Config endpoint is working"
else
    echo "❌ Config endpoint failed"
fi

# Test experts endpoint
echo "👥 Testing experts endpoint..."
if curl -f http://localhost/v1/experts/ > /dev/null 2>&1; then
    echo "✅ Experts endpoint is working"
else
    echo "❌ Experts endpoint failed"
fi

echo ""
echo "🎉 Docker deployment test completed!"
echo ""
echo "📋 Available endpoints:"
echo "   - API: http://localhost/v1/"
echo "   - Health: http://localhost/v1/health/"
echo "   - Admin: http://localhost/admin/"
echo "   - Docs: See README.md for full API documentation"
echo ""
echo "🔑 Default admin credentials:"
echo "   - Email: admin@tinrate.com"
echo "   - Password: admin123"
echo ""
echo "📊 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"