#!/bin/bash

# Fix script for Kubernetes deployment issues
# This script updates the k8s deployment files to use correct images

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔧 Fixing Kubernetes deployment configuration...${NC}"

# Fix backend-deployment.yaml
echo "Fixing backend-deployment.yaml..."
sed -i.bak 's|image: python:3.11-slim|image: mbskafld/ai-video-chaptering-backend:latest|g' k8s/backend-deployment.yaml

# Fix celery-worker-deployment.yaml if needed
if grep -q "python:3.11-slim" k8s/celery-worker-deployment.yaml; then
    echo "Fixing celery-worker-deployment.yaml..."
    sed -i.bak 's|image: python:3.11-slim|image: mbskafld/ai-video-chaptering-backend:latest|g' k8s/celery-worker-deployment.yaml
fi

# Fix frontend-deployment.yaml if needed
if grep -q "node:18-alpine" k8s/frontend-deployment.yaml; then
    echo "Fixing frontend-deployment.yaml..."
    sed -i.bak 's|image: node:18-alpine|image: mbskafld/ai-video-chaptering-frontend:latest|g' k8s/frontend-deployment.yaml
fi

# Update kustomization.yaml to use Docker Hub images
echo "Updating kustomization.yaml..."
cat > k8s/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ai-video-chaptering

resources:
- namespace.yaml
- configmap.yaml
- secrets.yaml
- persistent-volumes.yaml
- backend-deployment.yaml
- celery-worker-deployment.yaml
- celery-flower-deployment.yaml
- frontend-deployment.yaml
- ingress.yaml
- database-init-job.yaml

commonLabels:
  app: ai-video-chaptering
  version: v1.0.0

images:
- name: python:3.11-slim
  newName: mbskafld/ai-video-chaptering-backend
  newTag: latest
- name: node:18-alpine  
  newName: mbskafld/ai-video-chaptering-frontend
  newTag: latest

replicas:
- name: backend-api
  count: 2
- name: celery-worker
  count: 2
- name: frontend
  count: 3
- name: celery-flower
  count: 1
EOF

echo -e "${GREEN}✅ Kubernetes configuration fixed!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the changes in k8s/*.yaml files"
echo "2. Update k8s/secrets.yaml with your actual values"
echo "3. Deploy using: kubectl apply -k k8s/"
echo ""
echo "To use DigitalOcean registry instead of Docker Hub:"
echo "- Update image references to: registry.digitalocean.com/skafldstudio/..."
echo "- Fix the k8s-deploy.sh script to build correct Dockerfiles"