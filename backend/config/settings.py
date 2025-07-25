"""
Flask application configuration for AI Video Chaptering service
"""

import os
from datetime import timedelta
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Upload Settings
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max file size
    UPLOAD_FOLDER = BASE_DIR.parent / 'storage' / 'uploads'
    PROCESSED_FOLDER = BASE_DIR.parent / 'storage' / 'processed'
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
    
    # AI Model Settings
    LLAMA_MODEL_PATH = os.environ.get('LLAMA_MODEL_PATH', 'meta-llama/Llama-3.1-8B-Instruct')
    ASR_MODEL = os.environ.get('ASR_MODEL', 'large-v3')  # Whisper model
    CHAPTER_MODEL_PATH = os.environ.get('CHAPTER_MODEL_PATH', '')  # LoRA adapter path
    
    # Processing Settings
    MAX_CONCURRENT_JOBS = int(os.environ.get('MAX_CONCURRENT_JOBS', '2'))
    JOB_TIMEOUT = int(os.environ.get('JOB_TIMEOUT', '7200'))  # 2 hours in seconds
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', '3600'))  # 1 hour
    
    # Redis Settings (for job queue)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Database Settings (SQLite for simplicity, can upgrade to PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f'sqlite:///{BASE_DIR / "app.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS Settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # WebSocket Settings
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    SOCKETIO_ASYNC_MODE = 'threading'
    
    # Logging Settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    
    # JWT Settings (for future authentication)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        # Create directories if they don't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PROCESSED_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FILE.parent, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Override with production settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production environment")
    
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for production environment")
    
    # Production-specific settings
    MAX_CONCURRENT_JOBS = int(os.environ.get('MAX_CONCURRENT_JOBS', '1'))
    RATELIMIT_DEFAULT = "50 per hour"

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Test-specific settings
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB for tests
    JOB_TIMEOUT = 300  # 5 minutes for tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 