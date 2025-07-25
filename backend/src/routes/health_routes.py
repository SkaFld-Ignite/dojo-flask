"""
Health check routes for API monitoring
"""

from flask import Blueprint, jsonify
from ..models import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'service': 'ai-video-chaptering',
        'version': '1.0.0'
    })

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with database connectivity"""
    
    health_status = {
        'success': True,
        'status': 'healthy',
        'service': 'ai-video-chaptering',
        'version': '1.0.0',
        'checks': {}
    }
    
    # Database check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['success'] = False
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Additional checks can be added here (Redis, disk space, etc.)
    
    status_code = 200 if health_status['success'] else 503
    return jsonify(health_status), status_code

@health_bp.route('/api/v1/status', methods=['GET'])
def api_status():
    """API status endpoint"""
    return jsonify({
        'success': True,
        'api_version': 'v1',
        'endpoints': {
            'videos': '/api/v1/videos',
            'chapters': '/api/v1/chapters',
            'processing': '/api/v1/processing'
        },
        'documentation': '/docs'
    }) 