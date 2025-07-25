#!/bin/bash

# Local Development Setup Script for AI Video Chaptering App
# This script sets up the local environment for testing before deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏗️ Setting up local development environment${NC}"

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Checking project structure...${NC}"

# Create necessary directories
echo -e "${YELLOW}📁 Creating local directories...${NC}"
mkdir -p storage/uploads
mkdir -p storage/processed
mkdir -p models
mkdir -p logs

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp environment.template .env
    
    echo -e "${YELLOW}⚠️ Please edit .env file with your configuration before starting${NC}"
    echo "The following values need to be set:"
    echo "• SECRET_KEY (generate a secure random key)"
    echo "• POSTGRES_PASSWORD"
    echo "• Any other environment-specific values"
    
    read -p "Press Enter when you've configured .env file..."
fi

# Build and start services
echo -e "${BLUE}🐳 Building Docker containers...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose build
else
    docker compose build
fi

echo -e "${BLUE}🚀 Starting services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d postgres redis
else
    docker compose up -d postgres redis
fi

echo -e "${YELLOW}⏳ Waiting for databases to be ready...${NC}"
sleep 10

# Initialize database
echo -e "${BLUE}🗄️ Initializing database...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose run --rm backend python -m flask db upgrade
else
    docker compose run --rm backend python -m flask db upgrade
fi

# Start all services
echo -e "${BLUE}🎯 Starting all services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

echo -e "${GREEN}✅ Local environment setup complete!${NC}"

echo -e "\n${YELLOW}📊 Service Status:${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

echo -e "\n${YELLOW}🌐 Available Services:${NC}"
echo "• Backend API: http://localhost:8000"
echo "• Frontend: http://localhost:3000 (if running separately)"
echo "• Flower (Celery monitoring): http://localhost:5555"
echo "• PostgreSQL: localhost:5432"
echo "• Redis: localhost:6379"

echo -e "\n${YELLOW}🔧 Useful Commands:${NC}"
echo "• View logs: docker-compose logs -f [service-name]"
echo "• Stop services: docker-compose down"
echo "• Restart service: docker-compose restart [service-name]"
echo "• Run database migrations: docker-compose run --rm backend python -m flask db upgrade"
echo "• Access backend shell: docker-compose exec backend bash"

echo -e "\n${YELLOW}🧪 Test the API:${NC}"
echo "curl http://localhost:8000/api/health"

echo -e "\n${GREEN}🎉 Ready for development!${NC}"

# Test API health
echo -e "${BLUE}🏥 Testing API health...${NC}"
sleep 5
if curl -f http://localhost:8000/api/health &> /dev/null; then
    echo -e "${GREEN}✅ API is healthy and responding${NC}"
else
    echo -e "${RED}❌ API health check failed. Check logs with: docker-compose logs backend${NC}"
fi 