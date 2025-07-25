"""
WebSocket event handlers for real-time processing updates
"""

from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from .. import socketio
from ..models import ProcessingJob, Video

# Store active connections by job ID
active_connections = {}

def register_websocket_events():
    """Register WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        emit('connected', {'message': 'Connected to video processing service'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
        
        # Remove from all job rooms
        client_jobs = [job_id for job_id, clients in active_connections.items() 
                      if request.sid in clients]
        
        for job_id in client_jobs:
            if request.sid in active_connections[job_id]:
                active_connections[job_id].remove(request.sid)
            
            if not active_connections[job_id]:  # No more clients for this job
                del active_connections[job_id]
    
    @socketio.on('subscribe_job')
    def handle_subscribe_job(data):
        """Subscribe to job progress updates"""
        
        job_id = data.get('jobId')
        if not job_id:
            emit('error', {'message': 'Job ID required'})
            return
        
        # Validate job exists
        job = ProcessingJob.get_by_id(job_id)
        if not job:
            emit('error', {'message': 'Processing job not found'})
            return
        
        # Join job room
        room_name = f"job_{job_id}"
        join_room(room_name)
        
        # Track connection
        if job_id not in active_connections:
            active_connections[job_id] = []
        
        if request.sid not in active_connections[job_id]:
            active_connections[job_id].append(request.sid)
        
        # Send current job status
        video = Video.get_by_id(job.video_id)
        
        emit('job_status', {
            'job': job.to_dict(),
            'video': video.to_dict() if video else None
        })
        
        print(f"Client {request.sid} subscribed to job {job_id}")
    
    @socketio.on('unsubscribe_job')
    def handle_unsubscribe_job(data):
        """Unsubscribe from job progress updates"""
        
        job_id = data.get('jobId')
        if not job_id:
            emit('error', {'message': 'Job ID required'})
            return
        
        # Leave job room
        room_name = f"job_{job_id}"
        leave_room(room_name)
        
        # Remove from tracking
        if job_id in active_connections and request.sid in active_connections[job_id]:
            active_connections[job_id].remove(request.sid)
        
        if job_id in active_connections and not active_connections[job_id]:
            del active_connections[job_id]
        
        emit('unsubscribed', {'jobId': job_id})
        print(f"Client {request.sid} unsubscribed from job {job_id}")
    
    @socketio.on('subscribe_video')
    def handle_subscribe_video(data):
        """Subscribe to all processing jobs for a video"""
        
        video_id = data.get('videoId')
        if not video_id:
            emit('error', {'message': 'Video ID required'})
            return
        
        # Validate video exists
        video = Video.get_by_id(video_id)
        if not video:
            emit('error', {'message': 'Video not found'})
            return
        
        # Join video room
        room_name = f"video_{video_id}"
        join_room(room_name)
        
        # Get current jobs for video
        jobs = ProcessingJob.get_by_video(video_id)
        jobs_data = [job.to_dict() for job in jobs]
        
        emit('video_jobs', {
            'videoId': video_id,
            'jobs': jobs_data,
            'video': video.to_dict()
        })
        
        print(f"Client {request.sid} subscribed to video {video_id}")
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection health check"""
        emit('pong', {'timestamp': socketio.server.manager.get_current_timestamp()})

# Helper functions for emitting updates

def emit_job_progress(job_id, job_data, video_data=None):
    """Emit job progress update to subscribed clients"""
    
    room_name = f"job_{job_id}"
    
    socketio.emit('job_progress', {
        'job': job_data,
        'video': video_data
    }, room=room_name)
    
    # Also emit to video room if video_data is available
    if video_data:
        video_room = f"video_{video_data['id']}"
        socketio.emit('video_job_update', {
            'job': job_data,
            'video': video_data
        }, room=video_room)
    
    print(f"Emitted progress update for job {job_id}")

def emit_job_stage_change(job_id, job_data, video_data=None):
    """Emit job stage change to subscribed clients"""
    
    room_name = f"job_{job_id}"
    
    socketio.emit('job_stage_change', {
        'job': job_data,
        'video': video_data,
        'newStage': job_data.get('status'),
        'stageDescription': job_data.get('status_description')
    }, room=room_name)
    
    # Also emit to video room
    if video_data:
        video_room = f"video_{video_data['id']}"
        socketio.emit('video_job_stage_change', {
            'job': job_data,
            'video': video_data
        }, room=video_room)
    
    print(f"Emitted stage change for job {job_id}: {job_data.get('status')}")

def emit_job_complete(job_id, job_data, video_data=None, chapters_data=None):
    """Emit job completion to subscribed clients"""
    
    room_name = f"job_{job_id}"
    
    socketio.emit('job_complete', {
        'job': job_data,
        'video': video_data,
        'chapters': chapters_data or []
    }, room=room_name)
    
    # Also emit to video room
    if video_data:
        video_room = f"video_{video_data['id']}"
        socketio.emit('video_job_complete', {
            'job': job_data,
            'video': video_data,
            'chapters': chapters_data or []
        }, room=video_room)
    
    print(f"Emitted completion for job {job_id}")

def emit_job_error(job_id, job_data, video_data=None, error_message=None):
    """Emit job error to subscribed clients"""
    
    room_name = f"job_{job_id}"
    
    socketio.emit('job_error', {
        'job': job_data,
        'video': video_data,
        'error': error_message or job_data.get('error_message'),
        'errorDetails': job_data.get('error_details')
    }, room=room_name)
    
    # Also emit to video room
    if video_data:
        video_room = f"video_{video_data['id']}"
        socketio.emit('video_job_error', {
            'job': job_data,
            'video': video_data,
            'error': error_message or job_data.get('error_message')
        }, room=video_room)
    
    print(f"Emitted error for job {job_id}: {error_message}")

def get_active_job_connections():
    """Get count of active connections per job"""
    return {job_id: len(clients) for job_id, clients in active_connections.items()}

def broadcast_system_message(message, level='info'):
    """Broadcast system message to all connected clients"""
    
    socketio.emit('system_message', {
        'message': message,
        'level': level,
        'timestamp': socketio.server.manager.get_current_timestamp()
    }, broadcast=True)
    
    print(f"Broadcasted system message: {message}")

# Integration functions for use in processing routes

def notify_job_update(job):
    """Notify clients of job update (called from processing routes)"""
    
    from ..models import Video, Chapter
    
    video = Video.get_by_id(job.video_id)
    video_data = video.to_dict() if video else None
    
    if job.is_complete and job.status.value == 'complete':
        # Job completed successfully
        chapters = Chapter.get_by_video(job.video_id)
        chapters_data = [chapter.to_dict() for chapter in chapters]
        emit_job_complete(job.id, job.to_dict(), video_data, chapters_data)
    
    elif job.status.value == 'error':
        # Job failed
        emit_job_error(job.id, job.to_dict(), video_data)
    
    else:
        # Job progress update
        emit_job_progress(job.id, job.to_dict(), video_data)

def notify_stage_change(job, old_stage):
    """Notify clients of stage change (called from processing routes)"""
    
    from ..models import Video
    
    video = Video.get_by_id(job.video_id)
    video_data = video.to_dict() if video else None
    
    emit_job_stage_change(job.id, job.to_dict(), video_data) 