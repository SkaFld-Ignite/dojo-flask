#!/bin/bash

# Script to update Kubernetes secrets from .env file
# This reads your .env file and updates k8s/secrets.yaml

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Updating Kubernetes secrets from .env file${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create one first.${NC}"
    exit 1
fi

# Source the .env file (handle special characters)
export $(grep -v '^#' .env | grep -v '^$' | xargs -d '\n')

echo -e "${BLUE}📝 Reading environment variables from .env...${NC}"

# Generate a new secrets.yaml file
cat > k8s/secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: ai-video-chaptering-secrets
  namespace: ai-video-chaptering
type: Opaque
stringData:
  # Flask Configuration
  SECRET_KEY: "${SECRET_KEY}"
  
  # Database Configuration
  DATABASE_URL: "${DATABASE_URL}"
  REDIS_URL: "${REDIS_URL}"
  
  # Celery Configuration
  CELERY_BROKER_URL: "${CELERY_BROKER_URL}"
  CELERY_RESULT_BACKEND: "${CELERY_RESULT_BACKEND}"
  
  # DigitalOcean Spaces Configuration
  DO_SPACES_ENDPOINT: "${DO_SPACES_ENDPOINT}"
  DO_SPACES_BUCKET: "${DO_SPACES_BUCKET}"
  DO_SPACES_ACCESS_KEY: "${DO_SPACES_ACCESS_KEY}"
  DO_SPACES_SECRET_KEY: "${DO_SPACES_SECRET_KEY}"
  
  # Flower Monitoring (set secure values)
  FLOWER_USER: "admin"
  FLOWER_PASSWORD: "\${FLOWER_PASSWORD:-secure-flower-password}"
  
  # Optional: Monitoring and Error Tracking
  SENTRY_DSN: "${SENTRY_DSN:-}"
  
  # Frontend API URLs
  NEXT_PUBLIC_API_URL: "https://api.ai-video-chaptering.skafldstudio.com"
  NEXT_PUBLIC_WS_URL: "wss://api.ai-video-chaptering.skafldstudio.com"
EOF

echo -e "${GREEN}✅ k8s/secrets.yaml updated with values from .env${NC}"

echo -e "\n${YELLOW}⚠️ IMPORTANT: Please verify and update these values in your .env file:${NC}"
echo -e "${BLUE}1. SECRET_KEY:${NC} Generate a secure key (32+ characters)"
echo -e "${BLUE}2. DATABASE_URL:${NC} Your actual PostgreSQL connection string"
echo -e "${BLUE}3. REDIS_URL:${NC} Your actual Redis connection string"
echo -e "${BLUE}4. DO_SPACES_*:${NC} Your DigitalOcean Spaces credentials"
echo -e "${BLUE}5. FLOWER_PASSWORD:${NC} Set a secure password for Flower monitoring"

echo -e "\n${PURPLE}💡 Example values:${NC}"
echo -e "${BLUE}DATABASE_URL:${NC} postgresql://doadmin:password@db-postgresql-sfo3-12345.db.ondigitalocean.com:25060/video_chaptering?sslmode=require"
echo -e "${BLUE}REDIS_URL:${NC} rediss://default:password@db-redis-sfo3-12345.db.ondigitalocean.com:25061"

echo -e "\n${GREEN}🚀 After updating your .env file, run this script again to update the secrets.${NC}" 