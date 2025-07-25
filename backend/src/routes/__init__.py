"""
Route registration for Flask application
"""

from flask import Flask
from .health_routes import health_bp
from .video_routes import video_bp
from .chapter_routes import chapter_bp
from .processing_routes import processing_bp
from .ai_routes import ai_bp

def register_routes(app: Flask):
    """Register all route blueprints"""
    
    # Health check routes
    app.register_blueprint(health_bp, url_prefix='/api/health')
    
    # Video management routes
    app.register_blueprint(video_bp, url_prefix='/api/videos')
    
    # Chapter management routes
    app.register_blueprint(chapter_bp, url_prefix='/api/chapters')
    
    # Processing status routes
    app.register_blueprint(processing_bp, url_prefix='/api/processing')
    
    # AI processing routes
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    
    # Register WebSocket events
    from .websocket_events import register_websocket_events
    register_websocket_events() 