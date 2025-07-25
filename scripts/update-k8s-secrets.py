#!/usr/bin/env python3
"""
Update Kubernetes secrets.yaml file with values from .env file
"""

import os
import sys
from pathlib import Path

def load_env_file(env_path):
    """Load environment variables from .env file"""
    env_vars = {}
    
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at {env_path}")
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    
    return env_vars

def update_secrets_yaml(secrets_path, env_vars):
    """Update the k8s/secrets.yaml file with environment variables"""
    
    # Template for secrets.yaml
    secrets_template = f'''apiVersion: v1
kind: Secret
metadata:
  name: ai-video-chaptering-secrets
  namespace: ai-video-chaptering
type: Opaque
stringData:
  # Flask Configuration
  SECRET_KEY: "{env_vars.get('SECRET_KEY', '')}"
  
  # Database Configuration
  DATABASE_URL: "{env_vars.get('DATABASE_URL', '')}"
  REDIS_URL: "{env_vars.get('REDIS_URL', '')}"
  
  # Celery Configuration
  CELERY_BROKER_URL: "{env_vars.get('CELERY_BROKER_URL', '')}"
  CELERY_RESULT_BACKEND: "{env_vars.get('CELERY_RESULT_BACKEND', '')}"
  
  # DigitalOcean Spaces Configuration
  DO_SPACES_ENDPOINT: "{env_vars.get('DO_SPACES_ENDPOINT', '')}"
  DO_SPACES_BUCKET: "{env_vars.get('DO_SPACES_BUCKET', '')}"
  DO_SPACES_ACCESS_KEY: "{env_vars.get('DO_SPACES_ACCESS_KEY', '')}"
  DO_SPACES_SECRET_KEY: "{env_vars.get('DO_SPACES_SECRET_KEY', '')}"
  
  # Flower Monitoring
  FLOWER_USER: "{env_vars.get('FLOWER_USER', 'admin')}"
  FLOWER_PASSWORD: "{env_vars.get('FLOWER_PASSWORD', 'secure-flower-password')}"
  
  # Monitoring
  SENTRY_DSN: "{env_vars.get('SENTRY_DSN', '')}"
  
  # Frontend Configuration
  NEXT_PUBLIC_API_URL: "https://api.ai-video-chaptering.skafldstudio.com"
  NEXT_PUBLIC_WS_URL: "wss://api.ai-video-chaptering.skafldstudio.com"
'''
    
    # Write the updated secrets file
    with open(secrets_path, 'w') as f:
        f.write(secrets_template)
    
    print(f"✅ Updated {secrets_path}")

def main():
    """Main function"""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    secrets_path = project_root / 'k8s' / 'secrets.yaml'
    
    print("🔐 Updating Kubernetes secrets from .env file")
    
    # Load environment variables
    env_vars = load_env_file(env_path)
    
    if not env_vars:
        print("❌ No environment variables loaded from .env file")
        sys.exit(1)
    
    print(f"📝 Loaded {len(env_vars)} environment variables")
    
    # Update secrets.yaml
    update_secrets_yaml(secrets_path, env_vars)
    
    print("\n🎉 SUCCESS: k8s/secrets.yaml updated with values from .env")
    print("\n💡 Next steps:")
    print("1. Review the secrets.yaml file to ensure all values are correct")
    print("2. Deploy to Kubernetes: ./scripts/k8s-deploy.sh production")

if __name__ == '__main__':
    main() 