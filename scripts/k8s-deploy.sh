#!/bin/bash

# Kubernetes Deployment Script for AI Video Chaptering
# Deploys to existing DigitalOcean Kubernetes cluster: skafldstudio-remotedev

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="do-sfo3-skafldstudio-remotedev"
NAMESPACE="ai-video-chaptering"
KUBECONFIG_FILE="skafldstudio-remotedev-kubeconfig.yaml"
REGISTRY="registry.digitalocean.com/skafldstudio"

# Get environment from command line argument
ENVIRONMENT=${1:-production}

echo -e "${GREEN}🚀 Starting Kubernetes deployment to ${CLUSTER_NAME}${NC}"
echo -e "${PURPLE}Environment: ${ENVIRONMENT}${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed. Please install kubectl first.${NC}"
        exit 1
    fi
    
    # Check if kustomize is installed
    if ! command -v kustomize &> /dev/null; then
        echo -e "${RED}❌ kustomize is not installed. Please install kustomize first.${NC}"
        exit 1
    fi
    
    # Check if kubeconfig file exists
    if [ ! -f "${KUBECONFIG_FILE}" ]; then
        echo -e "${RED}❌ Kubeconfig file ${KUBECONFIG_FILE} not found.${NC}"
        exit 1
    fi
    
    # Check if doctl is installed (for registry access)
    if ! command -v doctl &> /dev/null; then
        echo -e "${RED}❌ doctl is not installed. Please install doctl first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to configure kubectl
setup_kubectl() {
    echo -e "${BLUE}⚙️ Setting up kubectl context...${NC}"
    
    export KUBECONFIG="${KUBECONFIG_FILE}"
    
    # Test cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Connected to cluster: $(kubectl config current-context)${NC}"
}

# Function to setup DigitalOcean registry authentication
setup_registry_auth() {
    echo -e "${BLUE}🔐 Setting up DigitalOcean registry authentication...${NC}"
    
    # Create registry secret for pulling images
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Create or update registry secret
    doctl registry kubernetes-manifest --namespace ${NAMESPACE} | kubectl apply -f -
    
    echo -e "${GREEN}✅ Registry authentication configured${NC}"
}

# Function to create external database services (if using managed databases)
create_external_services() {
    echo -e "${BLUE}🗄️ Setting up external database services...${NC}"
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: postgres-external
  namespace: ${NAMESPACE}
spec:
  type: ExternalName
  externalName: your-postgres-cluster.db.ondigitalocean.com
  ports:
  - port: 25060
    targetPort: 25060
    protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: redis-external
  namespace: ${NAMESPACE}
spec:
  type: ExternalName
  externalName: your-redis-cluster.db.ondigitalocean.com
  ports:
  - port: 25061
    targetPort: 25061
    protocol: TCP
EOF
    
    echo -e "${GREEN}✅ External database services created${NC}"
}

# Function to build and push Docker images
build_and_push_images() {
    echo -e "${BLUE}🐳 Building and pushing Docker images...${NC}"
    
    # Build backend image
    echo -e "${YELLOW}Building backend image...${NC}"
    docker build -t ${REGISTRY}/ai-video-chaptering-backend:latest -f Dockerfile .
    docker push ${REGISTRY}/ai-video-chaptering-backend:latest
    
    # Build frontend image
    echo -e "${YELLOW}Building frontend image...${NC}"
    docker build -t ${REGISTRY}/ai-video-chaptering-frontend:latest -f Dockerfile.frontend .
    docker push ${REGISTRY}/ai-video-chaptering-frontend:latest
    
    echo -e "${GREEN}✅ Images built and pushed successfully${NC}"
}

# Function to deploy application using kustomize
deploy_application() {
    echo -e "${BLUE}🚀 Deploying application to Kubernetes...${NC}"
    
    cd k8s
    
    # Apply all resources using kustomize
    kustomize build . | kubectl apply -f -
    
    cd ..
    
    echo -e "${GREEN}✅ Application deployed successfully${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${BLUE}🗄️ Running database migrations...${NC}"
    
    # Wait for migration job to complete
    kubectl wait --for=condition=complete job/database-migration -n ${NAMESPACE} --timeout=300s
    
    echo -e "${GREEN}✅ Database migrations completed${NC}"
}

# Function to preload AI models
preload_models() {
    echo -e "${BLUE}🤖 Preloading AI models...${NC}"
    
    # Wait for model preload job to complete
    kubectl wait --for=condition=complete job/model-preload -n ${NAMESPACE} --timeout=600s
    
    echo -e "${GREEN}✅ AI models preloaded${NC}"
}

# Function to check deployment status
check_deployment_status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    # Check pod status
    kubectl get pods -n ${NAMESPACE}
    
    # Check service status
    kubectl get services -n ${NAMESPACE}
    
    # Check ingress status
    kubectl get ingress -n ${NAMESPACE}
    
    echo -e "${GREEN}✅ Deployment status checked${NC}"
}

# Function to show application URLs
show_urls() {
    echo -e "\n${PURPLE}🌐 Application URLs:${NC}"
    echo -e "${GREEN}🖥️  Frontend:${NC} https://ai-video-chaptering.skafldstudio.com"
    echo -e "${GREEN}🔧  Backend API:${NC} https://api.ai-video-chaptering.skafldstudio.com"
    echo -e "${GREEN}🌸  Flower (Celery monitoring):${NC} https://flower.ai-video-chaptering.skafldstudio.com"
    echo -e "\n${YELLOW}💡 Note: Make sure your DNS is configured to point to your cluster's load balancer${NC}"
}

# Function to show useful commands
show_commands() {
    echo -e "\n${PURPLE}🔧 Useful Commands:${NC}"
    echo -e "${BLUE}View logs:${NC} kubectl logs -f deployment/backend-api -n ${NAMESPACE}"
    echo -e "${BLUE}Scale workers:${NC} kubectl scale deployment celery-worker --replicas=5 -n ${NAMESPACE}"
    echo -e "${BLUE}Check pod status:${NC} kubectl get pods -n ${NAMESPACE}"
    echo -e "${BLUE}Check services:${NC} kubectl get services -n ${NAMESPACE}"
    echo -e "${BLUE}Port forward API:${NC} kubectl port-forward svc/backend-api-service 8000:80 -n ${NAMESPACE}"
    echo -e "${BLUE}Port forward frontend:${NC} kubectl port-forward svc/frontend-service 3000:80 -n ${NAMESPACE}"
    echo -e "${BLUE}Delete deployment:${NC} kubectl delete namespace ${NAMESPACE}"
}

# Function to monitor deployment
monitor_deployment() {
    echo -e "${BLUE}👀 Monitoring deployment progress...${NC}"
    
    # Wait for deployments to be ready
    kubectl rollout status deployment/backend-api -n ${NAMESPACE}
    kubectl rollout status deployment/celery-worker -n ${NAMESPACE}
    kubectl rollout status deployment/frontend -n ${NAMESPACE}
    kubectl rollout status deployment/celery-flower -n ${NAMESPACE}
    
    echo -e "${GREEN}✅ All deployments are ready${NC}"
}

# Main deployment flow
case "${ENVIRONMENT}" in
    "production"|"prod")
        echo -e "${YELLOW}🏭 Production deployment${NC}"
        check_prerequisites
        setup_kubectl
        setup_registry_auth
        create_external_services
        build_and_push_images
        deploy_application
        run_migrations
        preload_models
        monitor_deployment
        check_deployment_status
        show_urls
        show_commands
        ;;
    "staging"|"stage")
        echo -e "${YELLOW}🧪 Staging deployment${NC}"
        check_prerequisites
        setup_kubectl
        setup_registry_auth
        create_external_services
        deploy_application
        run_migrations
        monitor_deployment
        check_deployment_status
        show_urls
        show_commands
        ;;
    "status")
        setup_kubectl
        check_deployment_status
        ;;
    "logs")
        setup_kubectl
        echo -e "${BLUE}📋 Recent logs from backend-api:${NC}"
        kubectl logs --tail=50 deployment/backend-api -n ${NAMESPACE}
        echo -e "${BLUE}📋 Recent logs from celery-worker:${NC}"
        kubectl logs --tail=50 deployment/celery-worker -n ${NAMESPACE}
        ;;
    "delete")
        setup_kubectl
        echo -e "${RED}⚠️ Deleting entire application...${NC}"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kubectl delete namespace ${NAMESPACE}
            echo -e "${GREEN}✅ Application deleted${NC}"
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid environment. Use: production, staging, status, logs, or delete${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 Kubernetes deployment completed successfully!${NC}" 