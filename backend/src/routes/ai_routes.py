"""
AI-specific API routes for processing control and model management
"""

from flask import Blueprint, request, jsonify, current_app
from ..models import Video, ProcessingJob
from ..utils.response_utils import success_response, error_response, validation_error_response
from ..ai.processing_pipeline import (
    start_video_processing,
    get_processing_status,
    cancel_processing,
    restart_processing,
    get_all_active_jobs,
    cleanup_processing_jobs
)
from ..ai.model_manager import ModelManager

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/process', methods=['POST'])
def start_processing():
    """Start AI processing for a video"""
    
    data = request.get_json()
    if not data or 'videoId' not in data:
        return validation_error_response(['videoId is required'])
    
    video_id = data['videoId']
    
    # Validate video exists
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    try:
        # Extract processing options
        processing_options = {
            'min_chapter_length': data.get('minChapterLength', 30.0),
            'max_chapters': data.get('maxChapters', 15),
            'transcription_language': data.get('language'),
            'initial_prompt': data.get('initialPrompt')
        }
        
        # Remove None values
        processing_options = {k: v for k, v in processing_options.items() if v is not None}
        
        # Start processing
        result = start_video_processing(video_id, processing_options)
        
        return success_response(result, message='Processing started successfully')
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Processing start failed: {str(e)}")
        return error_response('Failed to start processing', 500)

@ai_bp.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get AI processing status"""
    
    try:
        result = get_processing_status(job_id)
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        current_app.logger.error(f"Status retrieval failed: {str(e)}")
        return error_response('Failed to get processing status', 500)

@ai_bp.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel AI processing job"""
    
    try:
        result = cancel_processing(job_id)
        return success_response(result, message='Processing cancelled successfully')
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Processing cancellation failed: {str(e)}")
        return error_response('Failed to cancel processing', 500)

@ai_bp.route('/restart/<job_id>', methods=['POST'])
def restart_job(job_id):
    """Restart failed AI processing job"""
    
    try:
        result = restart_processing(job_id)
        return success_response(result, message='Processing restarted successfully')
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Processing restart failed: {str(e)}")
        return error_response('Failed to restart processing', 500)

@ai_bp.route('/jobs/active', methods=['GET'])
def get_active_jobs():
    """Get all active AI processing jobs"""
    
    try:
        jobs = get_all_active_jobs()
        
        return success_response({
            'activeJobs': jobs,
            'totalActive': len(jobs)
        })
        
    except Exception as e:
        current_app.logger.error(f"Active jobs retrieval failed: {str(e)}")
        return error_response('Failed to get active jobs', 500)

@ai_bp.route('/estimate', methods=['POST'])
def estimate_processing_time():
    """Estimate processing time for a video"""
    
    data = request.get_json()
    if not data or 'videoId' not in data:
        return validation_error_response(['videoId is required'])
    
    video_id = data['videoId']
    
    # Validate video exists
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    try:
        from ..ai.chapter_processor import ChapterProcessor
        
        processor = ChapterProcessor()
        estimates = processor.estimate_processing_time(video)
        requirements = processor.get_processing_requirements()
        
        return success_response({
            'videoId': video_id,
            'duration': video.duration,
            'estimates': estimates,
            'requirements': requirements
        })
        
    except Exception as e:
        current_app.logger.error(f"Processing estimation failed: {str(e)}")
        return error_response('Failed to estimate processing time', 500)

@ai_bp.route('/models/status', methods=['GET'])
def get_model_status():
    """Get AI model loading status"""
    
    try:
        model_manager = ModelManager()
        
        status = {
            'device': model_manager.device,
            'models_loaded': list(model_manager._models.keys()) if hasattr(model_manager, '_models') else [],
            'memory_usage': model_manager.get_memory_usage(),
            'model_cache_dir': str(model_manager.model_cache_dir)
        }
        
        return success_response(status)
        
    except Exception as e:
        current_app.logger.error(f"Model status retrieval failed: {str(e)}")
        return error_response('Failed to get model status', 500)

@ai_bp.route('/models/load', methods=['POST'])
def load_models():
    """Preload AI models"""
    
    data = request.get_json()
    load_asr = data.get('loadAsr', True) if data else True
    load_llm = data.get('loadLlm', False) if data else False
    
    try:
        model_manager = ModelManager()
        loaded_models = []
        
        if load_asr:
            try:
                model_manager.get_asr_model()
                loaded_models.append('asr')
            except Exception as e:
                current_app.logger.warning(f"Failed to load ASR model: {str(e)}")
        
        if load_llm:
            try:
                model_manager.get_llm_model()
                loaded_models.append('llm')
            except Exception as e:
                current_app.logger.warning(f"Failed to load LLM model: {str(e)}")
        
        return success_response({
            'loaded_models': loaded_models,
            'memory_usage': model_manager.get_memory_usage()
        }, message=f'Loaded {len(loaded_models)} models successfully')
        
    except Exception as e:
        current_app.logger.error(f"Model loading failed: {str(e)}")
        return error_response('Failed to load models', 500)

@ai_bp.route('/models/unload', methods=['POST'])
def unload_models():
    """Unload AI models to free memory"""
    
    data = request.get_json()
    unload_asr = data.get('unloadAsr', True) if data else True
    unload_llm = data.get('unloadLlm', True) if data else True
    
    try:
        model_manager = ModelManager()
        unloaded_models = []
        
        if unload_asr and model_manager.is_model_loaded('asr'):
            model_manager.unload_model('asr')
            unloaded_models.append('asr')
        
        if unload_llm and model_manager.is_model_loaded('llm'):
            model_manager.unload_model('llm')
            unloaded_models.append('llm')
        
        return success_response({
            'unloaded_models': unloaded_models,
            'memory_usage': model_manager.get_memory_usage()
        }, message=f'Unloaded {len(unloaded_models)} models successfully')
        
    except Exception as e:
        current_app.logger.error(f"Model unloading failed: {str(e)}")
        return error_response('Failed to unload models', 500)

@ai_bp.route('/config', methods=['GET'])
def get_processing_config():
    """Get current AI processing configuration"""
    
    try:
        from ..ai.chapter_processor import ChapterProcessor
        
        processor = ChapterProcessor()
        config = processor.get_config()
        
        return success_response({
            'config': config,
            'device': processor.model_manager.device
        })
        
    except Exception as e:
        current_app.logger.error(f"Config retrieval failed: {str(e)}")
        return error_response('Failed to get processing configuration', 500)

@ai_bp.route('/config', methods=['POST'])
def update_processing_config():
    """Update AI processing configuration"""
    
    data = request.get_json()
    if not data:
        return error_response('No configuration data provided', 400)
    
    try:
        from ..ai.chapter_processor import ChapterProcessor
        
        processor = ChapterProcessor()
        processor.update_config(data)
        
        return success_response({
            'config': processor.get_config()
        }, message='Configuration updated successfully')
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Config update failed: {str(e)}")
        return error_response('Failed to update configuration', 500)

@ai_bp.route('/cleanup', methods=['POST'])
def cleanup_resources():
    """Clean up AI processing resources"""
    
    data = request.get_json()
    cleanup_models = data.get('cleanupModels', True) if data else True
    cleanup_jobs = data.get('cleanupJobs', True) if data else True
    max_age_days = data.get('maxAgeDays', 30) if data else 30
    
    try:
        cleanup_results = {}
        
        # Clean up models
        if cleanup_models:
            model_manager = ModelManager()
            model_manager.unload_all_models()
            cleanup_results['models_unloaded'] = True
        
        # Clean up old jobs
        if cleanup_jobs:
            job_cleanup = cleanup_processing_jobs(max_age_days)
            cleanup_results.update(job_cleanup)
        
        return success_response(cleanup_results, message='Cleanup completed successfully')
        
    except Exception as e:
        current_app.logger.error(f"Cleanup failed: {str(e)}")
        return error_response('Failed to clean up resources', 500) 