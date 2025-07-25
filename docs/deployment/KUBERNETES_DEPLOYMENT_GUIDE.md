# Kubernetes Deployment Guide

## ✅ What the Fix Script Did

The script successfully updated your Kubernetes configurations:

1. **Fixed backend-deployment.yaml**: Changed from generic `python:3.11-slim` to your actual Docker Hub image `mbskafld/ai-video-chaptering-backend:latest`

2. **Updated kustomization.yaml**: Now correctly maps base images to your Docker Hub images

## 📋 Next Steps for Kubernetes Deployment

### Step 1: Create/Update Secrets

First, generate secure values:

```bash
# Generate Flask secret key
python -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(32))"

# Generate Flower password
python -c "import secrets; print('FLOWER_PASSWORD:', secrets.token_urlsafe(16))"
```

### Step 2: Set Up External Services

#### Option A: Use DigitalOcean Managed Databases (Recommended)

1. **Create PostgreSQL Database:**
   ```bash
   doctl databases create ai-video-chaptering-db \
     --engine pg \
     --version 15 \
     --region sfo3 \
     --size db-s-1vcpu-1gb
   ```

2. **Create Redis Database:**
   ```bash
   doctl databases create ai-video-chaptering-redis \
     --engine redis \
     --version 7 \
     --region sfo3 \
     --size db-s-1vcpu-1gb
   ```

3. **Get Connection Strings:**
   ```bash
   # PostgreSQL
   doctl databases connection ai-video-chaptering-db --format "Connection string"
   
   # Redis
   doctl databases connection ai-video-chaptering-redis --format "Connection string"
   ```

#### Option B: Use In-Cluster Databases
If you want databases inside Kubernetes, you'll need to deploy PostgreSQL and Redis separately (not included in current config).

### Step 3: Create DigitalOcean Spaces

1. Go to: https://cloud.digitalocean.com/spaces
2. Create a new Space:
   - Name: `ai-video-chaptering`
   - Region: `sfo3` (same as your cluster)
3. Generate Access Keys:
   - Go to API → Spaces Keys
   - Generate New Key
   - Save the Access Key and Secret Key

### Step 4: Update secrets.yaml

Copy the example and update with your values:

```bash
cp k8s/secrets-example.yaml k8s/secrets.yaml
```

Then edit `k8s/secrets.yaml` with your actual values:
- Replace all CHANGE_ME values
- Add your database URLs
- Add your Spaces credentials
- Update domain names

### Step 5: Deploy to Kubernetes

```bash
# Set up kubectl context
export KUBECONFIG=skafldstudio-remotedev-kubeconfig.yaml

# Verify connection
kubectl cluster-info

# Deploy everything
kubectl apply -k k8s/

# Watch deployment progress
kubectl get pods -n ai-video-chaptering -w
```

### Step 6: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n ai-video-chaptering

# Check services
kubectl get svc -n ai-video-chaptering

# Check ingress (for your domain)
kubectl get ingress -n ai-video-chaptering

# View logs if needed
kubectl logs -n ai-video-chaptering deployment/backend-api
kubectl logs -n ai-video-chaptering deployment/celery-worker
```

## 🚨 Important Notes

### Docker Images
Your deployment is using Docker Hub images:
- Backend: `mbskafld/ai-video-chaptering-backend:latest`
- Frontend: `mbskafld/ai-video-chaptering-frontend:latest`

Make sure these images are:
1. Up to date with your latest code
2. Publicly accessible (or add image pull secrets)

### Domain Configuration
Update the ingress with your actual domain:
```bash
kubectl edit ingress -n ai-video-chaptering ai-video-chaptering-ingress
```

### SSL/TLS
The ingress is configured for cert-manager. Make sure you have:
1. cert-manager installed in your cluster
2. Correct email in the ingress annotation

## 🔧 Troubleshooting

If pods aren't starting:
```bash
# Describe pod for events
kubectl describe pod -n ai-video-chaptering <pod-name>

# Check logs
kubectl logs -n ai-video-chaptering <pod-name>

# Check secrets are created
kubectl get secrets -n ai-video-chaptering
```

If database connections fail:
- Verify connection strings in secrets
- Check if databases are in same region
- Ensure SSL mode is set correctly

## 🎯 Alternative: Use App Platform Instead

If Kubernetes seems complex, you can use the simpler DigitalOcean App Platform:

```bash
./scripts/deploy.sh complete
```

This will handle most of the infrastructure setup automatically!