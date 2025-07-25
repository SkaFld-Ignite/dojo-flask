# Kubernetes Deployment Guide

## Overview

This guide covers deploying the AI Video Chaptering application to your existing DigitalOcean Kubernetes cluster `skafldstudio-remotedev`.

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "DigitalOcean Kubernetes Cluster"
        subgraph "Ingress Layer"
            LB[Load Balancer]
            Ingress[NGINX Ingress]
            Cert[Cert-Manager]
        end
        
        subgraph "Application Pods"
            Frontend[Frontend Pods x3]
            Backend[Backend API Pods x2]
            Workers[Celery Worker Pods x2]
            Flower[Flower Monitor Pod]
        end
        
        subgraph "Storage"
            PV1[Models Storage PV]
            PV2[Logs Storage PV]
            PV3[Temp Storage PV]
        end
    end
    
    subgraph "External Services"
        PostgreSQL[Managed PostgreSQL]
        Redis[Managed Redis]
        Spaces[DigitalOcean Spaces]
    end
    
    Users --> LB
    LB --> Ingress
    Ingress --> Frontend
    Ingress --> Backend
    Backend --> PostgreSQL
    Backend --> Redis
    Backend --> Spaces
    Workers --> Redis
    Workers --> Spaces
    Workers --> PV1
    Backend --> PV2
    Workers --> PV3
```

## 🚀 Quick Start

### 1. Cluster Setup (One-time)

```bash
# Set up ingress controller, cert-manager, and other components
./scripts/setup-cluster.sh
```

### 2. Configure Secrets

Edit `k8s/secrets.yaml` with your actual values:

```yaml
# Database connections
DATABASE_URL: "postgresql://user:pass@your-postgres.db.ondigitalocean.com:25060/video_chaptering?sslmode=require"
REDIS_URL: "rediss://user:pass@your-redis.db.ondigitalocean.com:25061"

# DigitalOcean Spaces
DO_SPACES_ACCESS_KEY: "your-spaces-access-key"
DO_SPACES_SECRET_KEY: "your-spaces-secret-key"
DO_SPACES_BUCKET: "ai-video-chaptering-storage"

# Security
SECRET_KEY: "your-generated-secret-key"
FLOWER_USER: "admin"
FLOWER_PASSWORD: "secure-password"
```

### 3. Deploy Application

```bash
# Deploy to production
./scripts/k8s-deploy.sh production

# Deploy to staging
./scripts/k8s-deploy.sh staging
```

### 4. Configure DNS

Point your domains to the load balancer IP:

```bash
# Get load balancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Configure these DNS A records:
ai-video-chaptering.skafldstudio.com -> LOAD_BALANCER_IP
api.ai-video-chaptering.skafldstudio.com -> LOAD_BALANCER_IP
flower.ai-video-chaptering.skafldstudio.com -> LOAD_BALANCER_IP
```

## 📦 Components

### Deployments

| Component | Replicas | Resources | Purpose |
|-----------|----------|-----------|---------|
| Frontend | 3 | 256Mi/100m | Next.js UI |
| Backend API | 2 | 2Gi/1000m | Flask API + WebSocket |
| Celery Workers | 2 (auto-scale to 10) | 4Gi/2000m | AI Processing |
| Flower Monitor | 1 | 512Mi/500m | Job Monitoring |

### Storage

| Volume | Size | Purpose |
|--------|------|---------|
| ai-models-storage | 20Gi | AI model cache |
| app-logs-storage | 5Gi | Application logs |
| temp-storage | 50Gi | Video processing temp files |

### Networking

| Service | Type | Purpose |
|---------|------|---------|
| frontend-service | ClusterIP | Internal frontend access |
| backend-api-service | ClusterIP | Internal API access |
| celery-flower-service | ClusterIP | Internal monitoring access |
| Ingress | LoadBalancer | External HTTPS access |

## 🔧 Management Commands

### Deployment Management

```bash
# Check deployment status
./scripts/k8s-deploy.sh status

# View application logs
./scripts/k8s-deploy.sh logs

# Delete entire application
./scripts/k8s-deploy.sh delete
```

### Manual Operations

```bash
# Set kubeconfig
export KUBECONFIG=skafldstudio-remotedev-kubeconfig.yaml

# Check pod status
kubectl get pods -n ai-video-chaptering

# View logs for specific component
kubectl logs -f deployment/backend-api -n ai-video-chaptering
kubectl logs -f deployment/celery-worker -n ai-video-chaptering

# Scale workers manually
kubectl scale deployment celery-worker --replicas=5 -n ai-video-chaptering

# Port forward for local testing
kubectl port-forward svc/backend-api-service 8000:80 -n ai-video-chaptering
kubectl port-forward svc/frontend-service 3000:80 -n ai-video-chaptering

# Access pod shell
kubectl exec -it deployment/backend-api -n ai-video-chaptering -- bash

# View resource usage
kubectl top pods -n ai-video-chaptering
kubectl top nodes
```

### Database Operations

```bash
# Run database migrations manually
kubectl create job --from=cronjob/database-migration manual-migration -n ai-video-chaptering

# Access database via port forward
kubectl port-forward svc/postgres-external 5432:25060 -n ai-video-chaptering
# Then connect: psql -h localhost -p 5432 -U username video_chaptering
```

## 🔍 Monitoring and Troubleshooting

### Health Checks

```bash
# Check application health
curl https://api.ai-video-chaptering.skafldstudio.com/api/health

# Check ingress status
kubectl get ingress -n ai-video-chaptering

# Check certificate status
kubectl get certificate -n ai-video-chaptering
```

### Common Issues

#### 1. Pods Stuck in Pending
```bash
# Check node resources
kubectl describe nodes

# Check persistent volume claims
kubectl get pvc -n ai-video-chaptering

# Check storage class
kubectl get storageclass
```

#### 2. SSL Certificate Issues
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Check certificate details
kubectl describe certificate ai-video-chaptering-tls -n ai-video-chaptering

# Check Let's Encrypt challenge
kubectl get challenges -n ai-video-chaptering
```

#### 3. Image Pull Errors
```bash
# Check registry secret
kubectl get secret skafldstudio-registry -n ai-video-chaptering

# Recreate registry secret
doctl registry kubernetes-manifest --namespace ai-video-chaptering | kubectl apply -f -
```

#### 4. Database Connection Issues
```bash
# Test external service resolution
kubectl run test-pod --image=busybox -it --rm -- nslookup postgres-external.ai-video-chaptering.svc.cluster.local

# Check secret values
kubectl get secret ai-video-chaptering-secrets -n ai-video-chaptering -o yaml
```

## 📊 Auto-scaling

### Horizontal Pod Autoscaler (HPA)

The Celery workers are configured with HPA:

```yaml
minReplicas: 1
maxReplicas: 10
metrics:
- CPU: 70%
- Memory: 80%
```

### Cluster Autoscaling

DigitalOcean clusters can auto-scale nodes:

```bash
# Enable cluster autoscaling in DigitalOcean console
# Or via doctl:
doctl kubernetes cluster update skafldstudio-remotedev --auto-scale=true --min-nodes=1 --max-nodes=10
```

## 🔒 Security

### Network Policies

```bash
# Apply network policies (optional)
kubectl apply -f k8s/network-policies.yaml
```

### RBAC

```bash
# Create service account with limited permissions
kubectl apply -f k8s/rbac.yaml
```

### Pod Security Standards

```bash
# Enable pod security standards
kubectl label namespace ai-video-chaptering pod-security.kubernetes.io/enforce=restricted
```

## 💾 Backup and Recovery

### Database Backups

Managed PostgreSQL includes automatic backups. For additional backups:

```bash
# Manual backup job
kubectl create job pg-backup --image=postgres:15 -- pg_dump $DATABASE_URL > backup.sql
```

### Persistent Volume Backups

```bash
# Create volume snapshots (if supported)
kubectl apply -f k8s/volume-snapshots.yaml
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/k8s-deploy.yml
name: Deploy to Kubernetes
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Install doctl
      uses: digitalocean/action-doctl@v2
      with:
        token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
    - name: Build and push images
      run: |
        doctl registry login
        docker build -t registry.digitalocean.com/skafldstudio/ai-video-chaptering-backend:${{ github.sha }} -f Dockerfile.k8s .
        docker push registry.digitalocean.com/skafldstudio/ai-video-chaptering-backend:${{ github.sha }}
    - name: Deploy to Kubernetes
      run: |
        doctl kubernetes cluster kubeconfig save skafldstudio-remotedev
        ./scripts/k8s-deploy.sh production
```

## 📈 Performance Optimization

### Resource Optimization

```bash
# Monitor resource usage
kubectl top pods -n ai-video-chaptering --sort-by=memory
kubectl top pods -n ai-video-chaptering --sort-by=cpu

# Adjust resource requests/limits based on usage
kubectl edit deployment backend-api -n ai-video-chaptering
```

### Storage Optimization

```bash
# Enable volume expansion
kubectl patch pvc ai-models-storage -n ai-video-chaptering -p '{"spec":{"resources":{"requests":{"storage":"30Gi"}}}}'

# Use faster storage class for AI workloads
kubectl patch deployment celery-worker -n ai-video-chaptering -p '{"spec":{"template":{"spec":{"volumes":[{"name":"models-storage","persistentVolumeClaim":{"claimName":"ai-models-storage-fast"}}]}}}}'
```

## 🌍 Multi-Region Deployment

For global deployment:

```bash
# Deploy to multiple regions
./scripts/k8s-deploy.sh production --region=sfo3
./scripts/k8s-deploy.sh production --region=nyc3
./scripts/k8s-deploy.sh production --region=fra1
```

## 📋 Migration from App Platform

If migrating from App Platform:

1. **Export data** from existing deployment
2. **Update DNS** to point to new load balancer
3. **Run migration** to transfer persistent data
4. **Verify functionality** before decommissioning old deployment

This Kubernetes deployment provides enterprise-grade scalability, security, and observability for your AI Video Chaptering application. 