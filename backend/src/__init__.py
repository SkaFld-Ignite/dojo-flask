"""
Flask application factory for AI Video Chaptering service
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .models import db
from .routes import register_routes
from config.settings import get_config

# Initialize extensions
socketio = SocketIO()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    socketio.init_app(
        app, 
        cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'],
        async_mode=app.config['SOCKETIO_ASYNC_MODE']
    )
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    # Initialize app-specific config
    config_class.init_app(app)
    
    # Register routes
    register_routes(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'error': 'Bad request',
            'message': str(error.description)
        }, 400
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': 'Not found',
            'message': 'Resource not found'
        }, 404
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {
            'success': False,
            'error': 'File too large',
            'message': 'Uploaded file exceeds maximum size limit'
        }, 413
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            'success': False,
            'error': 'Rate limit exceeded',
            'message': f'Rate limit exceeded: {e.description}'
        }, 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }, 500

def register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize database"""
        db.create_all()
        print("Database initialized successfully!")
    
    @app.cli.command()
    def reset_db():
        """Reset database (WARNING: This will delete all data)"""
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")
    
    @app.cli.command()
    def create_test_data():
        """Create test data for development"""
        from .models import Video, Chapter, ProcessingJob
        from datetime import datetime
        import uuid
        
        # Create sample video
        video = Video(
            filename=f"sample_video_{uuid.uuid4().hex[:8]}.mp4",
            original_name="Sample Video.mp4",
            size=104857600,  # 100MB
            duration=3600,   # 1 hour
            format="mp4",
            mime_type="video/mp4",
            path="uploads/sample_video.mp4",
            processing_status="completed"
        )
        video.save()
        
        # Create sample chapters
        chapters_data = [
            {"title": "Introduction", "start_time": 0, "end_time": 300},
            {"title": "Main Content", "start_time": 300, "end_time": 2700},
            {"title": "Conclusion", "start_time": 2700, "end_time": 3600},
        ]
        
        for i, chapter_data in enumerate(chapters_data):
            chapter = Chapter(
                video_id=video.id,
                title=chapter_data["title"],
                start_time=chapter_data["start_time"],
                end_time=chapter_data["end_time"],
                confidence=0.85 + (i * 0.05),
                is_ai_generated=True,
                order=i + 1
            )
            chapter.save()
        
        print(f"Test data created! Video ID: {video.id}")

# Export for external access
__all__ = ['create_app', 'socketio'] 