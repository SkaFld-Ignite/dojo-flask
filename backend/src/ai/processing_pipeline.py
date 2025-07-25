"""
Complete processing pipeline for video chaptering with background job integration
"""

import os
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from celery import Celery
from celery.result import AsyncResult

from .chapter_processor import ChapterProcessor
from .model_manager import ModelManager
from ..models import Video, ProcessingJob, db
from ..routes.websocket_events import notify_job_update, notify_stage_change

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery('video_chaptering')

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3300,  # 55 minutes soft timeout
    worker_prefetch_multiplier=1,  # Process one task at a time
    task_acks_late=True,
    worker_disable_rate_limits=True
)

class ProcessingPipeline:
    """Main processing pipeline for video chaptering"""
    
    def __init__(self):
        self.processor = None  # Lazy initialization
    
    def get_processor(self) -> ChapterProcessor:
        """Get or create chapter processor instance"""
        if self.processor is None:
            self.processor = ChapterProcessor()
        return self.processor
    
    def start_processing(
        self,
        video_id: str,
        processing_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Start video processing in background
        
        Args:
            video_id: ID of the video to process
            processing_options: Optional processing configuration
            
        Returns:
            Dictionary with job information
        """
        
        try:
            # Get video
            video = Video.get_by_id(video_id)
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            # Check if video is already being processed
            existing_job = ProcessingJob.get_active_job_for_video(video_id)
            if existing_job:
                logger.warning(f"Video {video_id} is already being processed (job {existing_job.id})")
                return {
                    'job_id': existing_job.id,
                    'status': 'already_processing',
                    'message': 'Video is already being processed'
                }
            
            # Create processing job
            job = ProcessingJob(
                video_id=video_id,
                config=processing_options or {}
            )
            job.save()
            
            # Update video status
            video.processing_status = 'processing'
            video.save()
            
            # Start background task
            task_result = process_video_task.delay(video_id, job.id, processing_options)
            
            # Update job with task ID
            job.task_id = task_result.id
            job.save()
            
            logger.info(f"Started processing job {job.id} for video {video_id}")
            
            return {
                'job_id': job.id,
                'task_id': task_result.id,
                'status': 'started',
                'video_id': video_id,
                'estimated_time': self._estimate_processing_time(video)
            }
            
        except Exception as e:
            logger.error(f"Failed to start processing for video {video_id}: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get processing job status"""
        
        job = ProcessingJob.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        result = {
            'job': job.to_dict(),
            'video': None,
            'task_status': None
        }
        
        # Get video information
        video = Video.get_by_id(job.video_id)
        if video:
            result['video'] = video.to_dict()
        
        # Get Celery task status if available
        if job.task_id:
            try:
                task_result = AsyncResult(job.task_id, app=celery_app)
                result['task_status'] = {
                    'state': task_result.state,
                    'info': task_result.info if task_result.info else {}
                }
            except Exception as e:
                logger.warning(f"Failed to get task status for job {job_id}: {str(e)}")
        
        return result
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a processing job"""
        
        job = ProcessingJob.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.is_complete:
            raise ValueError("Cannot cancel completed job")
        
        try:
            # Revoke Celery task if it exists
            if job.task_id:
                celery_app.control.revoke(job.task_id, terminate=True)
            
            # Mark job as cancelled
            job.mark_error('Job cancelled by user')
            job.save()
            
            # Update video status
            video = Video.get_by_id(job.video_id)
            if video:
                video.processing_status = 'failed'
                video.save()
            
            # Notify via WebSocket
            notify_job_update(job)
            
            logger.info(f"Job {job_id} cancelled successfully")
            
            return {
                'job_id': job_id,
                'status': 'cancelled',
                'message': 'Job cancelled successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            raise
    
    def restart_job(self, job_id: str) -> Dict[str, Any]:
        """Restart a failed processing job"""
        
        job = ProcessingJob.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status.value != 'error':
            raise ValueError("Can only restart failed jobs")
        
        try:
            # Reset job state
            from ..models.processing_job import ProcessingStage
            
            job.status = ProcessingStage.UPLOADING
            job.progress = 0.0
            job.error_message = None
            job.error_details = None
            job.end_time = None
            job.start_time = datetime.utcnow()
            job.task_id = None
            
            # Reset stage progress
            job.stage_progress = {
                stage.value: 0.0 for stage in ProcessingStage
                if stage not in [ProcessingStage.COMPLETE, ProcessingStage.ERROR]
            }
            
            job.save()
            
            # Update video status
            video = Video.get_by_id(job.video_id)
            if video:
                video.processing_status = 'processing'
                video.save()
            
            # Start new background task
            task_result = process_video_task.delay(job.video_id, job.id, job.config)
            
            # Update job with new task ID
            job.task_id = task_result.id
            job.save()
            
            # Notify via WebSocket
            notify_job_update(job)
            
            logger.info(f"Job {job_id} restarted successfully")
            
            return {
                'job_id': job_id,
                'task_id': task_result.id,
                'status': 'restarted',
                'message': 'Job restarted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to restart job {job_id}: {str(e)}")
            raise
    
    def _estimate_processing_time(self, video: Video) -> Dict[str, float]:
        """Estimate processing time for a video"""
        
        processor = self.get_processor()
        return processor.estimate_processing_time(video)
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active processing jobs"""
        
        active_jobs = ProcessingJob.get_active_jobs()
        
        results = []
        for job in active_jobs:
            job_status = self.get_job_status(job.id)
            results.append(job_status)
        
        return results
    
    def cleanup_old_jobs(self, max_age_days: int = 30) -> Dict[str, Any]:
        """Clean up old completed/failed jobs"""
        
        try:
            from datetime import datetime, timedelta
            from ..models.processing_job import ProcessingStage
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            # Find old jobs
            old_jobs = ProcessingJob.query.filter(
                ProcessingJob.status.in_([ProcessingStage.COMPLETE, ProcessingStage.ERROR]),
                ProcessingJob.updated_at < cutoff_date
            ).all()
            
            # Delete old jobs
            cleanup_count = 0
            for job in old_jobs:
                # Revoke task if still exists
                if job.task_id:
                    try:
                        celery_app.control.revoke(job.task_id, terminate=False)
                    except Exception:
                        pass  # Task might not exist anymore
                
                job.delete()
                cleanup_count += 1
            
            logger.info(f"Cleaned up {cleanup_count} old jobs")
            
            return {
                'cleaned_up_jobs': cleanup_count,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Job cleanup failed: {str(e)}")
            raise

# Celery task for video processing
@celery_app.task(bind=True, name='process_video')
def process_video_task(self, video_id: str, job_id: str, processing_options: Dict[str, Any] = None):
    """
    Celery task for processing video chapters
    
    Args:
        video_id: ID of the video to process
        job_id: ID of the processing job
        processing_options: Processing configuration options
    """
    
    job = None
    try:
        # Get job and update status
        job = ProcessingJob.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Update job status to processing
        from ..models.processing_job import ProcessingStage
        old_stage = job.status
        job.status = ProcessingStage.PROCESSING
        job.save()
        
        # Notify stage change
        notify_stage_change(job, old_stage)
        
        # Create progress callback
        def progress_callback(progress: float, message: str):
            """Update job progress and notify clients"""
            try:
                job.update_progress(progress=progress, metadata={'message': message})
                job.save()
                
                # Notify via WebSocket
                notify_job_update(job)
                
                # Update Celery task state
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'progress': progress,
                        'message': message,
                        'job_id': job_id
                    }
                )
                
            except Exception as e:
                logger.warning(f"Failed to update progress: {str(e)}")
        
        # Initialize processor
        processor = ChapterProcessor()
        
        # Apply processing options if provided
        if processing_options:
            processor.update_config(processing_options)
        
        # Process video
        result = processor.process_video(
            video_id=video_id,
            job_id=job_id,
            progress_callback=progress_callback,
            config_overrides=processing_options
        )
        
        # Update video status
        video = Video.get_by_id(video_id)
        if video:
            video.processing_status = 'completed'
            video.save()
        
        logger.info(f"Video processing completed for job {job_id}")
        
        return result
        
    except Exception as e:
        error_message = f"Processing failed: {str(e)}"
        logger.error(f"Video processing failed for job {job_id}: {error_message}")
        
        # Update job with error
        if job:
            job.mark_error(error_message, str(e))
            job.save()
            
            # Update video status
            video = Video.get_by_id(video_id)
            if video:
                video.processing_status = 'failed'
                video.save()
            
            # Notify error via WebSocket
            notify_job_update(job)
        
        # Re-raise for Celery
        raise self.retry(exc=e, countdown=60, max_retries=3)

# Create pipeline instance
pipeline = ProcessingPipeline()

# Export functions for use in routes
def start_video_processing(video_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Start video processing"""
    return pipeline.start_processing(video_id, options)

def get_processing_status(job_id: str) -> Dict[str, Any]:
    """Get processing job status"""
    return pipeline.get_job_status(job_id)

def cancel_processing(job_id: str) -> Dict[str, Any]:
    """Cancel processing job"""
    return pipeline.cancel_job(job_id)

def restart_processing(job_id: str) -> Dict[str, Any]:
    """Restart processing job"""
    return pipeline.restart_job(job_id)

def get_all_active_jobs() -> List[Dict[str, Any]]:
    """Get all active jobs"""
    return pipeline.get_active_jobs()

def cleanup_processing_jobs(max_age_days: int = 30) -> Dict[str, Any]:
    """Clean up old jobs"""
    return pipeline.cleanup_old_jobs(max_age_days) 