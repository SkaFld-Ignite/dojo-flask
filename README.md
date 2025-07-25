# AI Video Chaptering Application

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/your-username/ai-video-chaptering/tree/main)

An intelligent video chaptering application that automatically generates chapters for videos using AI models. Built with Next.js frontend and Flask backend, powered by faster-whisper for speech recognition and Llama models for intelligent chapter generation.

## 🎯 Features

### Core Functionality
- **Automated Chapter Generation**: AI-powered chapter detection using speech-to-text and LLM analysis
- **Real-time Processing**: Live progress updates with WebSocket integration
- **Interactive Video Player**: HTML5 player with chapter navigation and keyboard shortcuts
- **Chapter Management**: Full CRUD operations with drag-and-drop reordering
- **Multi-format Export**: JSON, SRT, VTT, CSV, and TXT export options
- **Background Processing**: Scalable job queue with Celery workers

### User Experience
- **Responsive Design**: Mobile-first design with desktop enhancements
- **Accessibility**: WCAG 2.1 AA compliant with screen reader support
- **Real-time Updates**: Live processing status and progress tracking
- **Error Handling**: Comprehensive error recovery and user feedback
- **Modern UI**: Clean, intuitive interface inspired by Notion and YouTube

### Technical Features
- **GPU Acceleration**: CUDA/MPS support for faster AI processing
- **Model Management**: Dynamic loading/unloading with memory optimization
- **File Validation**: Secure upload with metadata extraction
- **Type Safety**: Full TypeScript coverage for reliability
- **Production Ready**: Comprehensive logging, monitoring, and configuration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Processing │
│   (Next.js)     │◄──►│    (Flask)      │◄──►│    (Celery)     │
│                 │    │                 │    │                 │
│ • Video Upload  │    │ • API Routes    │    │ • Whisper STT   │
│ • Chapter UI    │    │ • WebSocket     │    │ • Llama LLM     │
│ • Real-time     │    │ • Database      │    │ • Background    │
│   Updates       │    │ • File Storage  │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Infrastructure │
                    │                 │
                    │ • PostgreSQL    │
                    │ • Redis         │
                    │ • File Storage  │
                    │ • Load Balancer │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm 9+
- **Python** 3.11+ with pip
- **Docker** and Docker Compose
- **DigitalOcean Account** (for production deployment)

### Local Development

**Option 1: Complete Local Environment (Mirrors Production)**
```bash
# Clone the repository
git clone https://github.com/your-username/ai-video-chaptering.git
cd ai-video-chaptering

# Set up complete environment with all services
chmod +x scripts/*.sh
./scripts/local-setup-complete.sh

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000  
# Load Balancer: http://localhost:80
# Flower (Celery): http://localhost:5555
# MinIO Console: http://localhost:9001
```

**Option 2: Basic Development Environment**
```bash
# Set up basic backend-only environment
./scripts/local-setup.sh

# Start frontend separately for development
npm install
npm run dev

# Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Flower: http://localhost:5555
```

## 📦 Deployment

### DigitalOcean Kubernetes (DOKS) - Recommended

**Kubernetes Deployment to Existing Cluster:**
```bash
# One-time cluster setup (ingress, cert-manager, etc.)
./scripts/setup-cluster.sh

# Deploy application to Kubernetes
./scripts/k8s-deploy.sh production

# Check deployment status  
./scripts/k8s-deploy.sh status

# View logs
./scripts/k8s-deploy.sh logs
```

### DigitalOcean App Platform (Alternative)

**Complete Deployment (Frontend + Backend on App Platform):**
```bash
# Deploy everything to DigitalOcean App Platform
./scripts/deploy.sh complete

# Check deployment status
./scripts/deploy.sh status

# View logs
./scripts/deploy.sh logs
```

**Manual Setup:**
1. **Install DigitalOcean CLI**
   ```bash
   # macOS
   brew install doctl
   
   # Linux
   curl -sL https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz | tar -xzv
   sudo mv doctl /usr/local/bin
   ```

2. **Authenticate**
   ```bash
   doctl auth init
   # Enter your API token from: https://cloud.digitalocean.com/account/api/tokens
   ```

3. **Deploy**
   ```bash
   # Update .do/app.yaml with your repository details
   # Then deploy
   doctl apps create --spec .do/app.yaml
   ```

For detailed deployment instructions, see [deployment-guide.md](deployment-guide.md)

### Alternative Deployment Options

- **DigitalOcean Kubernetes (DOKS)**: Full Kubernetes deployment on existing cluster (recommended)
- **DigitalOcean App Platform**: Managed platform deployment with auto-scaling  
- **Self-Hosted Kubernetes**: Deploy to any Kubernetes cluster (AWS EKS, GCP GKE, etc.)
- **Hybrid Deployment**: Frontend on Vercel, Backend on DigitalOcean
- **Self-Hosted Docker**: Complete Docker Compose deployment on any server

## 🛠️ Configuration

### Environment Variables

#### Required Variables:
```bash
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0
CORS_ORIGINS=https://your-frontend-domain.com
```

#### AI Configuration:
```bash
WHISPER_MODEL=base  # or tiny, small, medium, large
LLM_MODEL=microsoft/DialoGPT-medium
USE_GPU=false  # Set to true if GPU available
DEVICE=cpu  # or cuda, mps
```

#### Storage Configuration:
```bash
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com
DO_SPACES_BUCKET=your-bucket-name
DO_SPACES_ACCESS_KEY=your-access-key
DO_SPACES_SECRET_KEY=your-secret-key
```

### Frontend Configuration

**For Complete DigitalOcean Deployment:**
```bash
# Set in DigitalOcean App Platform console
NEXT_PUBLIC_API_URL=https://backend-api-your-app.ondigitalocean.app
NEXT_PUBLIC_WS_URL=wss://backend-api-your-app.ondigitalocean.app
```

**For Hybrid Deployment (Vercel Frontend):**
```bash
# .env.local for Next.js on Vercel
NEXT_PUBLIC_API_URL=https://your-backend.ondigitalocean.app
NEXT_PUBLIC_WS_URL=wss://your-backend.ondigitalocean.app
```

## 🧪 Testing

### Local Testing
```bash
# Start local environment
./scripts/local-setup.sh

# Test API health
curl http://localhost:8000/api/health

# Run type checking
npm run type-check
```

### Production Testing
```bash
# Check deployment status
./scripts/deploy.sh status

# View application logs
./scripts/deploy.sh logs

# Test production API
curl https://your-app.ondigitalocean.app/api/health
```

## 📊 Monitoring & Maintenance

### Health Checks
- **Backend Health**: `/api/health` endpoint
- **Database**: Automatic connection monitoring
- **Queue Status**: Celery flower interface
- **AI Models**: Model loading status endpoints

### Performance Monitoring
- **DigitalOcean Metrics**: Built-in monitoring dashboard
- **Application Logs**: Centralized logging with rotation
- **Error Tracking**: Optional Sentry integration
- **Resource Usage**: CPU, memory, and storage monitoring

### Scaling
```bash
# Scale backend instances
doctl apps update <app-id> --spec .do/app.yaml

# Resize database
doctl databases resize ai-video-chaptering-db --size db-s-2vcpu-4gb
```

## 💰 Cost Estimation

### Development Environment
- **Local**: Free (your hardware)
- **Basic Cloud**: ~$50/month

### Production Environment
| Component | Basic | Production | High Load |
|-----------|-------|------------|-----------|
| App Platform | $15 | $35 | $70 |
| Database | $15 | $50 | $100 |
| Redis | $15 | $25 | $50 |
| Storage | $5 | $20 | $50 |
| **Total** | **$50** | **$130** | **$270** |

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Set up local development environment: `./scripts/local-setup.sh`
4. Make your changes and test thoroughly
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards
- **TypeScript**: Strict mode enabled
- **ESLint**: Airbnb configuration
- **Prettier**: Automatic code formatting
- **Testing**: Comprehensive test coverage required
- **Documentation**: Update README and comments

## 📚 API Documentation

### Video Operations
```bash
POST /api/videos/upload          # Upload video file
GET  /api/videos                 # List videos
GET  /api/videos/{id}            # Get video details
GET  /api/videos/{id}/stream     # Stream video
DELETE /api/videos/{id}          # Delete video
```

### Chapter Operations
```bash
GET    /api/videos/{id}/chapters      # Get chapters
POST   /api/videos/{id}/chapters      # Create chapter
PUT    /api/chapters/{id}             # Update chapter
DELETE /api/chapters/{id}             # Delete chapter
POST   /api/chapters/export           # Export chapters
POST   /api/chapters/reorder          # Reorder chapters
```

### Processing Operations
```bash
POST /api/ai/process/{video_id}       # Start AI processing
GET  /api/processing/jobs             # List jobs
GET  /api/processing/jobs/{id}        # Get job status
POST /api/processing/jobs/{id}/cancel # Cancel job
```

### WebSocket Events
```javascript
// Real-time processing updates
socket.on('processing_progress', (data) => {
  console.log(`Progress: ${data.progress}%`);
});

socket.on('processing_complete', (data) => {
  console.log('Processing complete!', data.chapters);
});
```

## 🔧 Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check build logs
docker-compose logs backend

# Common fixes:
# - Verify Python dependencies
# - Check Docker permissions
# - Ensure sufficient disk space
```

#### Database Connection
```bash
# Test database connection
docker-compose exec backend python -c "from backend.src.models import db; print('DB OK')"

# Reset database
docker-compose run --rm backend python -m flask db upgrade
```

#### AI Model Issues
```bash
# Check model loading
docker-compose logs celery-worker

# Clear model cache
docker-compose run --rm backend rm -rf /app/models/*
```

### Support Resources
- **Documentation**: [deployment-guide.md](deployment-guide.md)
- **Issues**: [GitHub Issues](https://github.com/your-username/ai-video-chaptering/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ai-video-chaptering/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **faster-whisper**: High-performance speech recognition
- **Llama Models**: Advanced language models for chapter generation
- **Next.js**: React framework for modern web applications
- **Flask**: Lightweight Python web framework
- **DigitalOcean**: Cloud infrastructure and deployment platform

## 🚀 What's Next

- [ ] Real-time collaboration features
- [ ] Advanced AI model fine-tuning
- [ ] Mobile app development
- [ ] Integration with popular video platforms
- [ ] Advanced analytics and insights
- [ ] Multi-language support

---

**Ready to get started?** Follow the [Quick Start](#-quick-start) guide or check out the [deployment documentation](deployment-guide.md) for production setup.

For questions or support, please [open an issue](https://github.com/your-username/ai-video-chaptering/issues) or start a [discussion](https://github.com/your-username/ai-video-chaptering/discussions).
