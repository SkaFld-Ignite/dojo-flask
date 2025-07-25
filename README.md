# AI Video Chaptering Application

A full-stack application for automatically generating chapters for videos using AI.

## 📁 Project Structure

```
dojo-flask/
├── backend/              # Flask backend application
│   ├── src/             # Source code
│   ├── tests/           # Test files
│   ├── config/          # Configuration files
│   ├── Dockerfile       # Docker configuration for local development
│   ├── Dockerfile.k8s   # Docker configuration for Kubernetes
│   └── requirements.txt # Python dependencies
│
├── frontend/            # Next.js frontend application
│   ├── app/            # Next.js app directory
│   ├── public/         # Static assets
│   ├── Dockerfile      # Docker configuration for local development
│   ├── Dockerfile.k8s  # Docker configuration for Kubernetes
│   └── package.json    # Node dependencies
│
├── k8s/                 # Kubernetes configurations
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── secrets.yaml
│   └── ...
│
├── docs/                # Documentation
│   └── deployment/     # Deployment guides
│
├── storage/            # File storage
├── logs/               # Application logs
├── nginx/              # Nginx configuration
├── docker-compose.yml  # Local development orchestration
└── .env                # Environment variables (not in git)
```

## 🚀 Quick Start

### Local Development

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Run with Docker Compose:

```bash
docker-compose up
```

### Kubernetes Deployment

1. Build and push Docker images:

```bash
# Backend
cd backend
docker build -f Dockerfile.k8s -t your-registry/ai-video-chaptering-backend:latest .
docker push your-registry/ai-video-chaptering-backend:latest

# Frontend
cd ../frontend
docker build -f Dockerfile.k8s -t your-registry/ai-video-chaptering-frontend:latest .
docker push your-registry/ai-video-chaptering-frontend:latest
```

2. Deploy to Kubernetes:

```bash
kubectl apply -f k8s/
```

## 📖 Documentation

- [Kubernetes Deployment Guide](docs/deployment/KUBERNETES_DEPLOYMENT_GUIDE.md)
- [Deployment Status](docs/deployment/DEPLOYMENT_STATUS.md)
- [Docker & Kubernetes Review](docs/deployment/DOCKER_KUBERNETES_REVIEW.md)

## 🛠 Technology Stack

- **Backend**: Flask, SQLAlchemy, Celery, Redis
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Database**: PostgreSQL
- **AI/ML**: OpenAI API, Whisper
- **Infrastructure**: Docker, Kubernetes, Nginx
