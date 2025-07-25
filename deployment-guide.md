# DigitalOcean Deployment Guide

Complete guide to deploy the AI Video Chaptering application on DigitalOcean App Platform.

## 📋 Prerequisites

1. **DigitalOcean Account**: [Sign up here](https://cloud.digitalocean.com/)
2. **GitHub Repository**: Code must be in a GitHub repository
3. **doctl CLI**: DigitalOcean command-line tool
4. **Local Environment**: Docker for local testing

## 🛠️ Installation & Setup

### 1. Install DigitalOcean CLI (doctl)

**macOS:**
```bash
brew install doctl
```

**Linux:**
```bash
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz | tar -xzv
sudo mv doctl /usr/local/bin
```

**Windows:**
Download from [GitHub releases](https://github.com/digitalocean/doctl/releases)

### 2. Authenticate with DigitalOcean

```bash
doctl auth init
```
Enter your API token when prompted. Get your token from: [DigitalOcean API Tokens](https://cloud.digitalocean.com/account/api/tokens)

### 3. Test Local Environment

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Set up local development environment
./scripts/local-setup.sh
```

## 🚀 Deployment Options

### Option A: Complete DigitalOcean Deployment (Recommended)

**Full-Stack Deployment on DigitalOcean:**
1. **Update Configuration**
   ```bash
   # Edit the complete app configuration
   nano .do/app-complete.yaml
   
   # Update these values:
   # - repo: your-username/your-repo-name
   # - branch: main (or your deployment branch)
   ```

2. **Deploy Everything**
   ```bash
   # Deploy frontend + backend + infrastructure to DigitalOcean
   ./scripts/deploy.sh complete
   
   # Check status
   ./scripts/deploy.sh status
   ```

### Option B: Hybrid Deployment

**Backend on DigitalOcean, Frontend on Vercel:**
```bash
# Deploy backend only to DigitalOcean
./scripts/deploy.sh production

# Deploy frontend to Vercel separately
npm run deploy:vercel
```

### Option B: Manual Deployment

#### Step 1: Create Database

```bash
# PostgreSQL database
doctl databases create ai-video-chaptering-db \
  --engine pg \
  --version 15 \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Redis for job queuing
doctl databases create ai-video-chaptering-redis \
  --engine redis \
  --version 7 \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1
```

#### Step 2: Create DigitalOcean Spaces Bucket

1. Go to [DigitalOcean Spaces](https://cloud.digitalocean.com/spaces)
2. Create a new bucket: `ai-video-chaptering-storage`
3. Choose region: `NYC3`
4. Enable CDN (optional but recommended)
5. Note the endpoint URL and create access keys

#### Step 3: Deploy Application

```bash
# Deploy using the app spec
doctl apps create --spec .do/app.yaml
```

## ⚙️ Configuration

### Environment Variables

Set these in the DigitalOcean App Platform console:

#### Required Variables:
```bash
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:pass@host:port/dbname  # Auto-set by DO
REDIS_URL=redis://host:port/0  # Auto-set by DO
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

#### DigitalOcean Spaces:
```bash
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_BUCKET=ai-video-chaptering-storage
DO_SPACES_ACCESS_KEY=your-spaces-access-key
DO_SPACES_SECRET_KEY=your-spaces-secret-key
DO_SPACES_REGION=nyc3
```

#### Optional Variables:
```bash
SENTRY_DSN=your-sentry-dsn-for-monitoring
LOG_LEVEL=INFO
WHISPER_MODEL=base
LLM_MODEL=microsoft/DialoGPT-medium
```

### Frontend Configuration

If deploying frontend to Vercel:

```bash
# .env.local in your frontend
NEXT_PUBLIC_API_URL=https://your-backend-app.ondigitalocean.app
NEXT_PUBLIC_WS_URL=wss://your-backend-app.ondigitalocean.app
```

## 🔧 Post-Deployment Configuration

### 1. Domain Setup

1. Go to your app in DigitalOcean console
2. Navigate to "Settings" → "Domains"
3. Add your custom domain
4. Update DNS records as instructed
5. SSL certificate will be auto-generated

### 2. Database Initialization

The database migrations run automatically, but you can manually trigger them:

```bash
# Get your app ID
doctl apps list

# Run database migrations
doctl apps run-command <app-id> backend-api "python -m flask db upgrade"
```

### 3. Scaling Configuration

#### Backend Scaling:
- **Development**: basic-xxs (1 vCPU, 512MB RAM) - $5/month
- **Production**: basic-xs (1 vCPU, 1GB RAM) - $10/month
- **High Load**: basic-s (1 vCPU, 2GB RAM) - $20/month

#### Worker Scaling:
- **Basic**: 1 worker instance
- **High Load**: 2-3 worker instances

### 4. Database Scaling:

```bash
# Resize database if needed
doctl databases resize ai-video-chaptering-db \
  --size db-s-2vcpu-4gb \
  --num-nodes 1
```

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Check app status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs

# Check specific service logs
doctl apps logs <app-id> --type=run --component=backend-api
```

### Performance Monitoring

1. **Enable metrics** in DigitalOcean console
2. **Set up alerts** for:
   - High CPU usage (>80%)
   - Memory usage (>90%)
   - Database connections
   - Error rate increases

### Backup Strategy

1. **Database Backups**: Enabled by default in managed databases
2. **Spaces Backup**: Configure lifecycle policies
3. **Application Backup**: GitHub repository serves as source backup

## 💰 Cost Estimation

### Monthly Costs (USD):

| Component | Basic Setup | Production Setup |
|-----------|-------------|------------------|
| App Platform (Backend) | $10 | $20 |
| App Platform (Worker) | $5 | $15 |
| PostgreSQL Database | $15 | $50 |
| Redis | $15 | $25 |
| Spaces Storage | $5 | $20 |
| **Total** | **~$50** | **~$130** |

### Traffic-based scaling:
- Bandwidth: $0.01 per GB
- Database transfer: Free within same region
- Spaces CDN: $0.01 per GB

## 🛡️ Security Best Practices

### 1. Environment Variables
- Use DigitalOcean App Platform secrets for sensitive data
- Rotate secrets regularly
- Never commit secrets to version control

### 2. Database Security
- Enable SSL connections (enabled by default)
- Use connection pooling
- Regular security updates (automatic in managed databases)

### 3. Network Security
- Trusted sources only for database access
- Enable firewall rules if using Droplets
- Use HTTPS everywhere

### 4. Application Security
- Keep dependencies updated
- Enable rate limiting
- Use CORS properly
- Implement proper authentication

## 🔄 CI/CD Setup

### GitHub Actions Integration

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to DigitalOcean

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to DigitalOcean
        uses: digitalocean/app_action@v1.1.5
        with:
          app_name: ai-video-chaptering
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
```

### Automated Testing

```yaml
# Add to your workflow before deployment
- name: Run Tests
  run: |
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🚨 Troubleshooting

### Common Issues:

#### 1. Build Failures
```bash
# Check build logs
doctl apps logs <app-id> --type=build

# Common fixes:
# - Check Dockerfile syntax
# - Verify requirements.txt
# - Check Python version compatibility
```

#### 2. Database Connection Issues
```bash
# Verify database URL
doctl databases connection <db-id>

# Check app environment variables
doctl apps get <app-id>
```

#### 3. Memory Issues
```bash
# Monitor resource usage
doctl apps get <app-id> --format Spec.Services

# Scale up if needed:
# Edit .do/app.yaml and update instance_size_slug
```

#### 4. AI Model Loading Issues
```bash
# Check worker logs
doctl apps logs <app-id> --component=celery-worker

# Verify model cache directory permissions
# Check MODEL_CACHE_DIR environment variable
```

### Support Resources:

- [DigitalOcean Documentation](https://docs.digitalocean.com/products/app-platform/)
- [Community Forum](https://www.digitalocean.com/community/)
- [Status Page](https://status.digitalocean.com/)

## 📚 Additional Resources

### Documentation:
- [App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [Managed Databases](https://docs.digitalocean.com/products/databases/)
- [Spaces Object Storage](https://docs.digitalocean.com/products/spaces/)

### Tools:
- [App Platform Calculator](https://www.digitalocean.com/pricing/app-platform)
- [Database Calculator](https://www.digitalocean.com/pricing/managed-databases)
- [Monitoring Dashboard](https://cloud.digitalocean.com/monitoring)

---

## 🎉 Deployment Complete!

Your AI Video Chaptering application is now running on DigitalOcean! 

**Next Steps:**
1. Test all functionality with sample videos
2. Set up monitoring and alerts
3. Configure automated backups
4. Set up custom domain and SSL
5. Optimize performance based on usage patterns

For support or questions, refer to the troubleshooting section or contact DigitalOcean support. 