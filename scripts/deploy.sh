#!/bin/bash

# DigitalOcean Deployment Script for AI Video Chaptering App
# Usage: ./scripts/deploy.sh [dev|staging|production]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
APP_NAME="ai-video-chaptering"
REGION="nyc3"

# Determine app spec file based on environment
if [ "${ENVIRONMENT}" = "complete" ]; then
    APP_SPEC=".do/app-complete.yaml"
    APP_NAME="ai-video-chaptering-complete"
else
    APP_SPEC=".do/app.yaml"
fi

echo -e "${GREEN}🚀 Starting DigitalOcean deployment for ${ENVIRONMENT} environment${NC}"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}❌ doctl CLI is not installed. Please install it first:${NC}"
    echo "curl -sL https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz | tar -xzv"
    echo "sudo mv doctl /usr/local/bin"
    exit 1
fi

# Check if user is authenticated
if ! doctl auth whoami &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with DigitalOcean. Run: doctl auth init${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Deployment Checklist:${NC}"
echo "✓ Environment: ${ENVIRONMENT}"
echo "✓ App Name: ${APP_NAME}"
echo "✓ Region: ${REGION}"

# Function to create database cluster
create_database() {
    echo -e "${YELLOW}🗄️ Creating PostgreSQL database cluster...${NC}"
    
    if doctl databases list | grep -q "${APP_NAME}-db"; then
        echo -e "${GREEN}✓ Database cluster already exists${NC}"
    else
        doctl databases create ${APP_NAME}-db \
            --engine pg \
            --version 15 \
            --region ${REGION} \
            --size db-s-1vcpu-1gb \
            --num-nodes 1
        
        echo -e "${GREEN}✓ Database cluster created${NC}"
        echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
        sleep 60
    fi
}

# Function to create Redis cluster
create_redis() {
    echo -e "${YELLOW}📮 Creating Redis cluster...${NC}"
    
    if doctl databases list | grep -q "${APP_NAME}-redis"; then
        echo -e "${GREEN}✓ Redis cluster already exists${NC}"
    else
        doctl databases create ${APP_NAME}-redis \
            --engine redis \
            --version 7 \
            --region ${REGION} \
            --size db-s-1vcpu-1gb \
            --num-nodes 1
        
        echo -e "${GREEN}✓ Redis cluster created${NC}"
        echo -e "${YELLOW}⏳ Waiting for Redis to be ready...${NC}"
        sleep 60
    fi
}

# Function to create DigitalOcean Spaces bucket
create_spaces() {
    echo -e "${YELLOW}🪣 Creating DigitalOcean Spaces bucket...${NC}"
    
    BUCKET_NAME="${APP_NAME}-storage-${ENVIRONMENT}"
    
    # Check if bucket exists (this will fail if it doesn't exist, which is expected)
    if doctl spaces ls | grep -q "${BUCKET_NAME}"; then
        echo -e "${GREEN}✓ Spaces bucket already exists${NC}"
    else
        echo -e "${YELLOW}Creating bucket: ${BUCKET_NAME}${NC}"
        echo "Please create the bucket manually in the DigitalOcean console:"
        echo "1. Go to https://cloud.digitalocean.com/spaces"
        echo "2. Create bucket: ${BUCKET_NAME}"
        echo "3. Region: ${REGION}"
        echo "4. Enable CDN (optional)"
        read -p "Press Enter when bucket is created..."
    fi
}

# Function to deploy the app
deploy_app() {
    echo -e "${YELLOW}🚀 Deploying application...${NC}"
    
    # Check if app exists
    if doctl apps list | grep -q "${APP_NAME}"; then
        echo -e "${YELLOW}📦 Updating existing app...${NC}"
        APP_ID=$(doctl apps list --format ID,Name --no-header | grep "${APP_NAME}" | awk '{print $1}')
        doctl apps update ${APP_ID} --spec ${APP_SPEC}
    else
        echo -e "${YELLOW}🆕 Creating new app...${NC}"
        doctl apps create --spec ${APP_SPEC}
    fi
    
    echo -e "${GREEN}✓ Application deployment initiated${NC}"
}

# Function to show deployment status
show_status() {
    echo -e "${YELLOW}📊 Checking deployment status...${NC}"
    
    if doctl apps list | grep -q "${APP_NAME}"; then
        APP_ID=$(doctl apps list --format ID,Name --no-header | grep "${APP_NAME}" | awk '{print $1}')
        echo -e "${GREEN}App Status:${NC}"
        doctl apps get ${APP_ID}
        
        echo -e "\n${YELLOW}Live URL:${NC}"
        doctl apps get ${APP_ID} --format LiveURL --no-header
    else
        echo -e "${RED}❌ App not found${NC}"
    fi
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}📝 Recent deployment logs:${NC}"
    
    if doctl apps list | grep -q "${APP_NAME}"; then
        APP_ID=$(doctl apps list --format ID,Name --no-header | grep "${APP_NAME}" | awk '{print $1}')
        doctl apps logs ${APP_ID} --type=deploy
    else
        echo -e "${RED}❌ App not found${NC}"
    fi
}

# Main deployment process
case "${ENVIRONMENT}" in
    "dev"|"development")
        echo -e "${YELLOW}🔧 Development deployment${NC}"
        deploy_app
        ;;
    "staging")
        echo -e "${YELLOW}🧪 Staging deployment${NC}"
        create_database
        create_redis
        create_spaces
        deploy_app
        ;;
    "production")
        echo -e "${YELLOW}🏭 Production deployment (Backend only)${NC}"
        create_database
        create_redis
        create_spaces
        deploy_app
        ;;
    "complete")
        echo -e "${YELLOW}🌟 Complete deployment (Frontend + Backend on DigitalOcean)${NC}"
        create_database
        create_redis
        create_spaces
        deploy_app
        ;;
    "status")
        show_status
        exit 0
        ;;
    "logs")
        show_logs
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid environment. Use: dev, staging, production, complete, status, or logs${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 Deployment process completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Check deployment status: ./scripts/deploy.sh status"
echo "2. View logs: ./scripts/deploy.sh logs"
echo "3. Set up your domain and SSL certificate in the DigitalOcean console"
echo "4. Configure environment variables in the App Platform console"
echo "5. Set up monitoring and alerts"

echo -e "\n${YELLOW}Important URLs:${NC}"
echo "• DigitalOcean Console: https://cloud.digitalocean.com/apps"
echo "• Database Console: https://cloud.digitalocean.com/databases"
echo "• Spaces Console: https://cloud.digitalocean.com/spaces"

echo -e "\n${YELLOW}Environment Variables to Set:${NC}"
echo "• SECRET_KEY (generate a secure random key)"
echo "• DO_SPACES_ACCESS_KEY"
echo "• DO_SPACES_SECRET_KEY"
echo "• SENTRY_DSN (optional)"

show_status 