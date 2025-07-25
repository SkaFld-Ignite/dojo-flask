#!/bin/bash

# Complete Local Development Setup Script for AI Video Chaptering App
# This script sets up the complete environment that mirrors DigitalOcean deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌟 Setting up COMPLETE local development environment${NC}"
echo -e "${PURPLE}This mirrors the full DigitalOcean deployment architecture${NC}"

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
mkdir -p backups
mkdir -p nginx/conf.d
mkdir -p nginx/ssl

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp environment.template .env
    
    # Set development-specific defaults
    sed -i.bak 's/your-super-secret-key-change-this-in-production/dev-secret-key-local-only/' .env
    sed -i.bak 's/your-database-password/postgres/' .env
    sed -i.bak 's/minioadmin/minioadmin/' .env
    sed -i.bak 's/minioadmin123/minioadmin123/' .env
    
    echo -e "${GREEN}✅ Environment file created with development defaults${NC}"
    echo -e "${YELLOW}💡 You can edit .env file to customize configuration${NC}"
fi

# Create MinIO bucket setup script
cat > scripts/setup-minio.sh << 'EOF'
#!/bin/bash
# Wait for MinIO to be ready
sleep 10

# Install MinIO client
curl -o /tmp/mc https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x /tmp/mc

# Configure MinIO client
/tmp/mc alias set local http://minio:9000 minioadmin minioadmin123

# Create bucket
/tmp/mc mb local/ai-video-chaptering

# Set public policy for development
/tmp/mc anonymous set public local/ai-video-chaptering

echo "MinIO bucket setup complete"
EOF
chmod +x scripts/setup-minio.sh

# Build and start infrastructure services first
echo -e "${BLUE}🗄️ Starting infrastructure services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.complete.yml up -d postgres redis minio
else
    docker compose -f docker-compose.complete.yml up -d postgres redis minio
fi

echo -e "${YELLOW}⏳ Waiting for infrastructure to be ready...${NC}"
sleep 15

# Set up MinIO bucket
echo -e "${BLUE}🪣 Setting up MinIO storage...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.complete.yml run --rm backend-api bash -c "
        curl -o /tmp/mc https://dl.min.io/client/mc/release/linux-amd64/mc && 
        chmod +x /tmp/mc && 
        /tmp/mc alias set local http://minio:9000 minioadmin minioadmin123 && 
        /tmp/mc mb local/ai-video-chaptering || true &&
        echo 'MinIO setup complete'
    "
else
    docker compose -f docker-compose.complete.yml run --rm backend-api bash -c "
        curl -o /tmp/mc https://dl.min.io/client/mc/release/linux-amd64/mc && 
        chmod +x /tmp/mc && 
        /tmp/mc alias set local http://minio:9000 minioadmin minioadmin123 && 
        /tmp/mc mb local/ai-video-chaptering || true &&
        echo 'MinIO setup complete'
    "
fi

# Build application containers
echo -e "${BLUE}🐳 Building application containers...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.complete.yml build
else
    docker compose -f docker-compose.complete.yml build
fi

# Initialize database
echo -e "${BLUE}🗄️ Initializing database...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.complete.yml run --rm backend-api python -m flask db upgrade
else
    docker compose -f docker-compose.complete.yml run --rm backend-api python -m flask db upgrade
fi

# Start all services
echo -e "${BLUE}🚀 Starting all services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.complete.yml up -d
else
    docker compose -f docker-compose.complete.yml up -d
fi

echo -e "${GREEN}✅ Complete local environment setup finished!${NC}"

# Wait for services to be fully ready
echo -e "${YELLOW}⏳ Waiting for all services to be healthy...${NC}"
sleep 30

echo -e "\n${YELLOW}📊 Service Status:${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.complete.yml ps
else
    docker compose -f docker-compose.complete.yml ps
fi

echo -e "\n${PURPLE}🌐 Available Services:${NC}"
echo -e "${GREEN}🖥️  Frontend (Next.js):${NC} http://localhost:3000"
echo -e "${GREEN}🔧  Backend API (Flask):${NC} http://localhost:8000"
echo -e "${GREEN}⚖️  Load Balancer (Nginx):${NC} http://localhost:80"
echo -e "${GREEN}🌸  Flower (Celery monitoring):${NC} http://localhost:5555"
echo -e "${GREEN}📊  MinIO Console:${NC} http://localhost:9001 (admin/admin123)"
echo -e "${GREEN}🗄️  PostgreSQL:${NC} localhost:5432"
echo -e "${GREEN}📮  Redis:${NC} localhost:6379"

echo -e "\n${PURPLE}🔧 Management Commands:${NC}"
echo -e "${BLUE}View logs:${NC} docker-compose -f docker-compose.complete.yml logs -f [service-name]"
echo -e "${BLUE}Stop services:${NC} docker-compose -f docker-compose.complete.yml down"
echo -e "${BLUE}Restart service:${NC} docker-compose -f docker-compose.complete.yml restart [service-name]"
echo -e "${BLUE}Scale workers:${NC} docker-compose -f docker-compose.complete.yml up -d --scale celery-worker=3"
echo -e "${BLUE}Database shell:${NC} docker-compose -f docker-compose.complete.yml exec postgres psql -U postgres video_chaptering"
echo -e "${BLUE}Backend shell:${NC} docker-compose -f docker-compose.complete.yml exec backend-api bash"
echo -e "${BLUE}View nginx config:${NC} docker-compose -f docker-compose.complete.yml exec nginx cat /etc/nginx/nginx.conf"

echo -e "\n${PURPLE}🧪 Test Commands:${NC}"
echo -e "${BLUE}Frontend health:${NC} curl http://localhost:3000"
echo -e "${BLUE}Backend health:${NC} curl http://localhost:8000/api/health"
echo -e "${BLUE}Load balancer:${NC} curl http://localhost:80/api/health"
echo -e "${BLUE}Upload test:${NC} curl -X POST -F 'video=@test.mp4' http://localhost:80/api/videos/upload"

echo -e "\n${GREEN}🎉 Complete development environment ready!${NC}"
echo -e "${PURPLE}This setup mirrors the DigitalOcean production architecture${NC}"

# Test services health
echo -e "\n${BLUE}🏥 Testing service health...${NC}"
sleep 10

# Test frontend
if curl -f http://localhost:3000 &> /dev/null; then
    echo -e "${GREEN}✅ Frontend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Frontend not ready yet, check logs: docker-compose -f docker-compose.complete.yml logs frontend${NC}"
fi

# Test backend
if curl -f http://localhost:8000/api/health &> /dev/null; then
    echo -e "${GREEN}✅ Backend API is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Backend not ready yet, check logs: docker-compose -f docker-compose.complete.yml logs backend-api${NC}"
fi

# Test load balancer
if curl -f http://localhost:80/api/health &> /dev/null; then
    echo -e "${GREEN}✅ Load balancer is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Load balancer not ready yet, check logs: docker-compose -f docker-compose.complete.yml logs nginx${NC}"
fi

echo -e "\n${PURPLE}🎯 Next Steps:${NC}"
echo "1. Visit http://localhost:3000 to access the application"
echo "2. Upload a test video to verify AI processing"
echo "3. Monitor processing in Flower: http://localhost:5555"
echo "4. Check MinIO storage: http://localhost:9001"
echo "5. When ready for production, run: ./scripts/deploy.sh complete"

echo -e "\n${GREEN}🌟 Happy developing! Your complete AI video chaptering environment is ready!${NC}" 