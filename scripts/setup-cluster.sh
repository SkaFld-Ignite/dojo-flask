#!/bin/bash

# Cluster Setup Script for AI Video Chaptering
# Sets up necessary components on DigitalOcean Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

KUBECONFIG_FILE="skafldstudio-remotedev-kubeconfig.yaml"

echo -e "${GREEN}🔧 Setting up cluster components for AI Video Chaptering${NC}"

# Function to setup kubectl
setup_kubectl() {
    echo -e "${BLUE}⚙️ Setting up kubectl context...${NC}"
    
    export KUBECONFIG="${KUBECONFIG_FILE}"
    
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Connected to cluster: $(kubectl config current-context)${NC}"
}

# Function to install NGINX Ingress Controller
install_nginx_ingress() {
    echo -e "${BLUE}🌐 Installing NGINX Ingress Controller...${NC}"
    
    # Check if already installed
    if kubectl get namespace ingress-nginx &> /dev/null; then
        echo -e "${YELLOW}⚠️ NGINX Ingress Controller already installed${NC}"
        return
    fi
    
    # Install NGINX Ingress Controller for DigitalOcean
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/do/deploy.yaml
    
    # Wait for the ingress controller to be ready
    echo -e "${YELLOW}⏳ Waiting for NGINX Ingress Controller to be ready...${NC}"
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s
    
    echo -e "${GREEN}✅ NGINX Ingress Controller installed and ready${NC}"
}

# Function to install cert-manager for SSL certificates
install_cert_manager() {
    echo -e "${BLUE}🔒 Installing cert-manager for SSL certificates...${NC}"
    
    # Check if already installed
    if kubectl get namespace cert-manager &> /dev/null; then
        echo -e "${YELLOW}⚠️ cert-manager already installed${NC}"
        return
    fi
    
    # Install cert-manager
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    echo -e "${YELLOW}⏳ Waiting for cert-manager to be ready...${NC}"
    kubectl wait --namespace cert-manager \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/instance=cert-manager \
        --timeout=300s
    
    echo -e "${GREEN}✅ cert-manager installed and ready${NC}"
}

# Function to create Let's Encrypt cluster issuer
create_letsencrypt_issuer() {
    echo -e "${BLUE}🔑 Creating Let's Encrypt cluster issuer...${NC}"
    
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@skafldstudio.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    
    echo -e "${GREEN}✅ Let's Encrypt cluster issuer created${NC}"
}

# Function to create storage classes if needed
create_storage_classes() {
    echo -e "${BLUE}💾 Checking storage classes...${NC}"
    
    # DigitalOcean should already have these, but let's make sure
    if ! kubectl get storageclass do-block-storage-retain &> /dev/null; then
        cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: do-block-storage-retain
provisioner: dobs.csi.digitalocean.com
allowVolumeExpansion: true
reclaimPolicy: Retain
parameters:
  type: pd-ssd
EOF
        echo -e "${GREEN}✅ Storage class created${NC}"
    else
        echo -e "${YELLOW}⚠️ Storage class already exists${NC}"
    fi
}

# Function to install metrics server if not present
install_metrics_server() {
    echo -e "${BLUE}📊 Checking metrics server...${NC}"
    
    if ! kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        echo -e "${YELLOW}Installing metrics server...${NC}"
        kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
        
        # Wait for metrics server to be ready
        kubectl wait --namespace kube-system \
            --for=condition=ready pod \
            --selector=k8s-app=metrics-server \
            --timeout=300s
        
        echo -e "${GREEN}✅ Metrics server installed${NC}"
    else
        echo -e "${YELLOW}⚠️ Metrics server already installed${NC}"
    fi
}

# Function to show cluster information
show_cluster_info() {
    echo -e "\n${PURPLE}📊 Cluster Information:${NC}"
    echo -e "${BLUE}Cluster:${NC} $(kubectl config current-context)"
    echo -e "${BLUE}Nodes:${NC}"
    kubectl get nodes
    echo -e "\n${BLUE}Storage Classes:${NC}"
    kubectl get storageclass
    echo -e "\n${BLUE}Ingress Controllers:${NC}"
    kubectl get pods -n ingress-nginx
    echo -e "\n${BLUE}Cert Manager:${NC}"
    kubectl get pods -n cert-manager
}

# Function to get load balancer IP
get_load_balancer_ip() {
    echo -e "\n${PURPLE}🌐 Load Balancer Information:${NC}"
    echo -e "${YELLOW}⏳ Getting load balancer IP...${NC}"
    
    # Wait for load balancer to get an external IP
    kubectl get svc -n ingress-nginx ingress-nginx-controller
    
    EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo -e "${GREEN}✅ Load Balancer IP: ${EXTERNAL_IP}${NC}"
        echo -e "\n${YELLOW}📝 DNS Configuration Required:${NC}"
        echo -e "${BLUE}Add these DNS A records to your domain:${NC}"
        echo -e "ai-video-chaptering.skafldstudio.com -> ${EXTERNAL_IP}"
        echo -e "api.ai-video-chaptering.skafldstudio.com -> ${EXTERNAL_IP}"
        echo -e "flower.ai-video-chaptering.skafldstudio.com -> ${EXTERNAL_IP}"
    else
        echo -e "${YELLOW}⚠️ Load balancer IP not yet assigned. Please check again in a few minutes.${NC}"
    fi
}

# Main execution
echo -e "${GREEN}🚀 Starting cluster setup...${NC}"

setup_kubectl
install_nginx_ingress
install_cert_manager
create_letsencrypt_issuer
create_storage_classes
install_metrics_server
show_cluster_info
get_load_balancer_ip

echo -e "\n${GREEN}🎉 Cluster setup completed successfully!${NC}"
echo -e "\n${PURPLE}🎯 Next Steps:${NC}"
echo "1. Configure DNS records as shown above"
echo "2. Update the secrets in k8s/secrets.yaml with your actual values"
echo "3. Run: ./scripts/k8s-deploy.sh production"
echo "4. Monitor deployment: kubectl get pods -n ai-video-chaptering"

echo -e "\n${YELLOW}💡 Useful Commands:${NC}"
echo -e "${BLUE}Check ingress:${NC} kubectl get ingress -A"
echo -e "${BLUE}Check certificates:${NC} kubectl get certificate -A"
echo -e "${BLUE}View load balancer:${NC} kubectl get svc -n ingress-nginx" 