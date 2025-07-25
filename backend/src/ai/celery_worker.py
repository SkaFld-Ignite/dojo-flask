"""
Celery worker configuration and initialization for video processing
"""

import os
import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutdown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_celery_app() -> Celery:
    """Create and configure Celery application"""
    
    # Create Celery app
    celery_app = Celery('video_chaptering_worker')
    
    # Configure Celery
    celery_app.conf.update(
        # Broker and backend
        broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        
        # Serialization
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        
        # Timezone
        timezone='UTC',
        enable_utc=True,
        
        # Task settings
        task_track_started=True,
        task_time_limit=3600,  # 1 hour timeout
        task_soft_time_limit=3300,  # 55 minutes soft timeout
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        
        # Worker settings
        worker_prefetch_multiplier=1,  # Process one task at a time
        worker_disable_rate_limits=True,
        worker_max_tasks_per_child=10,  # Restart worker after 10 tasks to prevent memory leaks
        
        # Routing
        task_routes={
            'process_video': {'queue': 'video_processing'},
            'cleanup_tasks': {'queue': 'maintenance'},
        },
        
        # Result settings
        result_expires=3600,  # Results expire after 1 hour
        result_persistent=True,
        
        # Monitoring
        worker_send_task_events=True,
        task_send_sent_event=True,
        
        # Security
        worker_hijack_root_logger=False,
        worker_log_color=False,
    )
    
    # Import tasks to register them
    from .processing_pipeline import process_video_task
    
    return celery_app

# Create Celery app instance
celery_app = create_celery_app()

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handler for when worker is ready"""
    logger.info("Celery worker is ready and waiting for tasks")
    
    # Perform any initialization here
    try:
        # Pre-load models if configured
        if os.getenv('PRELOAD_MODELS', '').lower() == 'true':
            from .model_manager import ModelManager
            model_manager = ModelManager()
            
            logger.info("Pre-loading AI models...")
            
            # Load ASR model
            try:
                model_manager.get_asr_model()
                logger.info("ASR model pre-loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to pre-load ASR model: {str(e)}")
            
            # Load LLM model (might be memory intensive)
            if os.getenv('PRELOAD_LLM', '').lower() == 'true':
                try:
                    model_manager.get_llm_model()
                    logger.info("LLM model pre-loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to pre-load LLM model: {str(e)}")
        
    except Exception as e:
        logger.error(f"Worker initialization failed: {str(e)}")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handler for when worker is shutting down"""
    logger.info("Celery worker is shutting down...")
    
    try:
        # Clean up models and free memory
        from .model_manager import ModelManager
        model_manager = ModelManager()
        model_manager.unload_all_models()
        logger.info("Models unloaded successfully")
        
    except Exception as e:
        logger.error(f"Worker shutdown cleanup failed: {str(e)}")

# Configure logging for better debugging
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

if __name__ == '__main__':
    # Start worker if run directly
    celery_app.start() 