"""
Processing status and job control API routes
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

from ..models import ProcessingJob, Video, Chapter, db
from ..utils.response_utils import success_response, error_response

processing_bp = Blueprint('processing', __name__)

@processing_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get processing job status"""
    
    job = ProcessingJob.get_by_id(job_id)
    if not job:
        return error_response('Processing job not found', 404)
    
    # Get associated video and chapters
    video = Video.get_by_id(job.video_id)
    chapters = Chapter.get_by_video(job.video_id) if job.is_complete else []
    
    return success_response({
        'job': job.to_dict(),
        'video': video.to_dict() if video else None,
        'chapters': [chapter.to_dict() for chapter in chapters] if chapters else []
    })

@processing_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a processing job"""
    
    job = ProcessingJob.get_by_id(job_id)
    if not job:
        return error_response('Processing job not found', 404)
    
    if job.is_complete:
        return error_response('Cannot cancel completed job', 400)
    
    try:
        # Mark job as cancelled (error state)
        job.mark_error('Job cancelled by user')
        job.save()
        
        # TODO: Cancel actual background processing task
        # This would involve stopping the Celery task
        
        return success_response({
            'job': job.to_dict()
        }, message='Job cancelled successfully')
        
    except Exception as e:
        current_app.logger.error(f"Job cancellation error: {str(e)}")
        return error_response('Failed to cancel job', 500)

@processing_bp.route('/jobs/<job_id>/restart', methods=['POST'])
def restart_job(job_id):
    """Restart a failed processing job"""
    
    job = ProcessingJob.get_by_id(job_id)
    if not job:
        return error_response('Processing job not found', 404)
    
    if job.status.value != 'error':
        return error_response('Can only restart failed jobs', 400)
    
    try:
        # Reset job state
        from ..models.processing_job import ProcessingStage
        
        job.status = ProcessingStage.UPLOADING
        job.progress = 0.0
        job.error_message = None
        job.error_details = None
        job.end_time = None
        job.start_time = datetime.utcnow()
        
        # Reset stage progress
        job.stage_progress = {
            stage.value: 0.0 for stage in ProcessingStage
            if stage not in [ProcessingStage.COMPLETE, ProcessingStage.ERROR]
        }
        
        job.save()
        
        # TODO: Queue new background processing task
        
        return success_response({
            'job': job.to_dict()
        }, message='Job restarted successfully')
        
    except Exception as e:
        current_app.logger.error(f"Job restart error: {str(e)}")
        return error_response('Failed to restart job', 500)

@processing_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List processing jobs with filters"""
    
    # Query parameters
    video_id = request.args.get('videoId')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 per page
    
    # Build query
    query = ProcessingJob.query
    
    if video_id:
        # Validate video exists
        video = Video.get_by_id(video_id)
        if not video:
            return error_response('Video not found', 404)
        query = query.filter(ProcessingJob.video_id == video_id)
    
    if status:
        try:
            from ..models.processing_job import ProcessingStage
            status_enum = ProcessingStage(status)
            query = query.filter(ProcessingJob.status == status_enum)
        except ValueError:
            return error_response(f'Invalid status: {status}', 400)
    
    # Order by creation time (newest first)
    query = query.order_by(ProcessingJob.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    
    jobs_data = []
    for job in pagination.items:
        job_dict = job.to_dict()
        
        # Include video info
        video = Video.get_by_id(job.video_id)
        if video:
            job_dict['video'] = {
                'id': video.id,
                'filename': video.filename,
                'originalName': video.original_name,
                'duration': video.duration
            }
        
        jobs_data.append(job_dict)
    
    return success_response({
        'jobs': jobs_data,
        'pagination': {
            'page': pagination.page,
            'limit': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'hasNext': pagination.has_next,
            'hasPrev': pagination.has_prev
        }
    })

@processing_bp.route('/jobs/active', methods=['GET'])
def get_active_jobs():
    """Get all currently active (non-complete) jobs"""
    
    jobs = ProcessingJob.get_active_jobs()
    
    jobs_data = []
    for job in jobs:
        job_dict = job.to_dict()
        
        # Include video info
        video = Video.get_by_id(job.video_id)
        if video:
            job_dict['video'] = {
                'id': video.id,
                'filename': video.filename,
                'originalName': video.original_name,
                'duration': video.duration
            }
        
        jobs_data.append(job_dict)
    
    return success_response({
        'activeJobs': jobs_data,
        'totalActive': len(jobs_data)
    })

@processing_bp.route('/stats', methods=['GET'])
def get_processing_stats():
    """Get processing statistics"""
    
    try:
        from ..models.processing_job import ProcessingStage
        
        # Get counts by status
        stats = {
            'totalJobs': ProcessingJob.query.count(),
            'activeJobs': len(ProcessingJob.get_active_jobs()),
            'completedJobs': ProcessingJob.query.filter(ProcessingJob.status == ProcessingStage.COMPLETE).count(),
            'failedJobs': ProcessingJob.query.filter(ProcessingJob.status == ProcessingStage.ERROR).count(),
            'byStatus': {}
        }
        
        # Count by each status
        for stage in ProcessingStage:
            count = ProcessingJob.query.filter(ProcessingJob.status == stage).count()
            stats['byStatus'][stage.value] = count
        
        # Calculate success rate
        total_finished = stats['completedJobs'] + stats['failedJobs']
        if total_finished > 0:
            stats['successRate'] = round((stats['completedJobs'] / total_finished) * 100, 2)
        else:
            stats['successRate'] = 0.0
        
        # Get recent job activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_jobs = ProcessingJob.query.filter(ProcessingJob.created_at >= yesterday).count()
        stats['recentActivity'] = recent_jobs
        
        return success_response(stats)
        
    except Exception as e:
        current_app.logger.error(f"Processing stats error: {str(e)}")
        return error_response('Failed to get processing statistics', 500)

@processing_bp.route('/jobs/<job_id>/progress', methods=['POST'])
def update_job_progress(job_id):
    """Update job progress (internal API for processing workers)"""
    
    job = ProcessingJob.get_by_id(job_id)
    if not job:
        return error_response('Processing job not found', 404)
    
    data = request.get_json()
    if not data:
        return error_response('No progress data provided', 400)
    
    try:
        # Update progress based on provided data
        stage = data.get('stage')
        progress = data.get('progress')
        stage_progress = data.get('stageProgress')
        metadata = data.get('metadata')
        error_message = data.get('errorMessage')
        
        if error_message:
            job.mark_error(error_message, data.get('errorDetails'))
        else:
            if stage:
                from ..models.processing_job import ProcessingStage
                try:
                    stage_enum = ProcessingStage(stage)
                    job.update_progress(
                        stage=stage_enum,
                        progress=progress,
                        stage_progress=stage_progress,
                        metadata=metadata
                    )
                except ValueError:
                    return error_response(f'Invalid stage: {stage}', 400)
            else:
                job.update_progress(
                    progress=progress,
                    stage_progress=stage_progress,
                    metadata=metadata
                )
        
        job.save()
        
        # TODO: Emit WebSocket event for real-time updates
        
        return success_response({
            'job': job.to_dict()
        }, message='Progress updated successfully')
        
    except Exception as e:
        current_app.logger.error(f"Progress update error: {str(e)}")
        return error_response('Failed to update progress', 500)

@processing_bp.route('/jobs/<job_id>/complete', methods=['POST'])
def complete_job(job_id):
    """Mark job as complete (internal API for processing workers)"""
    
    job = ProcessingJob.get_by_id(job_id)
    if not job:
        return error_response('Processing job not found', 404)
    
    data = request.get_json()
    chapters_generated = data.get('chaptersGenerated', 0) if data else 0
    
    try:
        job.mark_complete(chapters_generated)
        job.save()
        
        # Update video status
        video = Video.get_by_id(job.video_id)
        if video:
            video.processing_status = 'completed'
            video.save()
        
        # TODO: Emit WebSocket event for completion
        
        return success_response({
            'job': job.to_dict()
        }, message='Job completed successfully')
        
    except Exception as e:
        current_app.logger.error(f"Job completion error: {str(e)}")
        return error_response('Failed to complete job', 500)

@processing_bp.route('/cleanup', methods=['POST'])
def cleanup_old_jobs():
    """Clean up old completed/failed jobs (admin endpoint)"""
    
    data = request.get_json()
    max_age_days = data.get('maxAgeDays', 30) if data else 30
    
    try:
        from datetime import datetime, timedelta
        from ..models.processing_job import ProcessingStage
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        # Find old completed/failed jobs
        old_jobs = ProcessingJob.query.filter(
            ProcessingJob.status.in_([ProcessingStage.COMPLETE, ProcessingStage.ERROR]),
            ProcessingJob.updated_at < cutoff_date
        ).all()
        
        # Delete old jobs
        cleanup_count = 0
        for job in old_jobs:
            job.delete()
            cleanup_count += 1
        
        return success_response({
            'cleanedUpJobs': cleanup_count,
            'cutoffDate': cutoff_date.isoformat()
        }, message=f'Cleaned up {cleanup_count} old jobs')
        
    except Exception as e:
        current_app.logger.error(f"Job cleanup error: {str(e)}")
        return error_response('Failed to clean up jobs', 500) 