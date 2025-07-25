"""
Video upload and management API routes
"""

import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from ..models import Video, ProcessingJob, db
from ..utils.file_utils import validate_video_file, get_video_metadata
from ..utils.response_utils import success_response, error_response

video_bp = Blueprint('videos', __name__)

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    """Upload a video file for processing"""
    
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return error_response('No file provided', 400)
        
        file = request.files['file']
        if file.filename == '':
            return error_response('No file selected', 400)
        
        # Validate file
        validation_result = validate_video_file(file)
        if not validation_result['valid']:
            return error_response(validation_result['error'], 400)
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Create upload path
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        file_path = upload_folder / unique_filename
        
        # Save file
        file.save(str(file_path))
        
        # Get video metadata
        metadata = get_video_metadata(str(file_path))
        
        # Create video record
        video = Video(
            filename=unique_filename,
            original_name=original_filename,
            size=file_path.stat().st_size,
            duration=metadata.get('duration'),
            format=file_extension.lstrip('.'),
            mime_type=file.content_type,
            path=str(file_path.relative_to(upload_folder.parent)),
            processing_status='pending',
            metadata=metadata
        )
        video.save()
        
        # Create processing job
        job = ProcessingJob(
            video_id=video.id,
            config={
                'generate_chapters': request.form.get('generate_chapters', 'true').lower() == 'true',
                'model': request.form.get('model', 'default')
            }
        )
        job.save()
        
        # TODO: Queue background processing task
        
        return success_response({
            'videoId': video.id,
            'jobId': job.id,
            'video': video.to_dict()
        }, message='Video uploaded successfully')
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return error_response('Upload failed', 500)

@video_bp.route('/<video_id>', methods=['GET'])
def get_video(video_id):
    """Get video information by ID"""
    
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    # Get latest processing job
    latest_job = ProcessingJob.get_latest_by_video(video_id)
    
    # Get chapters
    chapters = [chapter.to_dict() for chapter in video.chapters]
    
    return success_response({
        'video': video.to_dict(),
        'chapters': chapters,
        'processingJob': latest_job.to_dict() if latest_job else None
    })

@video_bp.route('/<video_id>/stream', methods=['GET'])
def stream_video(video_id):
    """Stream video file"""
    
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    # Security: Only serve files from upload directory
    upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
    video_path = Path(video.path)
    
    if not str(video_path).startswith(str(upload_folder)):
        return error_response('File access denied', 403)
    
    if not video_path.exists():
        return error_response('Video file not found', 404)
    
    return send_from_directory(
        video_path.parent,
        video_path.name,
        as_attachment=False,
        mimetype=video.mime_type
    )

@video_bp.route('/', methods=['GET'])
def list_videos():
    """List videos with pagination"""
    
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 per page
    sort_by = request.args.get('sortBy', 'created_at')
    sort_order = request.args.get('sortOrder', 'desc')
    
    # Build query
    query = Video.query
    
    # Apply sorting
    if hasattr(Video, sort_by):
        order_attr = getattr(Video, sort_by)
        if sort_order.lower() == 'desc':
            order_attr = order_attr.desc()
        query = query.order_by(order_attr)
    
    # Paginate
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    
    videos = [video.to_dict() for video in pagination.items]
    
    return success_response({
        'videos': videos,
        'pagination': {
            'page': pagination.page,
            'limit': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'hasNext': pagination.has_next,
            'hasPrev': pagination.has_prev
        }
    })

@video_bp.route('/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete video and associated data"""
    
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    try:
        # Delete physical file
        video_path = Path(video.path)
        if video_path.exists():
            video_path.unlink()
        
        # Delete database record (cascades to chapters and jobs)
        video.delete()
        
        return success_response(message='Video deleted successfully')
        
    except Exception as e:
        current_app.logger.error(f"Delete error: {str(e)}")
        return error_response('Delete failed', 500)

@video_bp.route('/<video_id>/metadata', methods=['PUT'])
def update_video_metadata(video_id):
    """Update video metadata"""
    
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)
    
    # Update allowed fields
    allowed_fields = ['original_name']
    for field in allowed_fields:
        if field in data:
            setattr(video, field, data[field])
    
    video.save()
    
    return success_response({
        'video': video.to_dict()
    }, message='Video metadata updated successfully') 