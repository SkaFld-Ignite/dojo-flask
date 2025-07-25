"""
Main chapter processor that orchestrates the complete AI workflow
"""

import os
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .asr_processor import ASRProcessor
from .llm_processor import LLMProcessor
from .model_manager import ModelManager
from ..models import Video, Chapter, ProcessingJob, db

logger = logging.getLogger(__name__)

class ChapterProcessor:
    """Main processor for end-to-end video chaptering"""
    
    def __init__(
        self,
        asr_model_size: str = "large-v3",
        llm_model_name: str = "meta-llama/Llama-3.1-8B-Instruct"
    ):
        self.model_manager = ModelManager()
        self.asr_processor = ASRProcessor(model_size=asr_model_size)
        self.llm_processor = LLMProcessor(model_name=llm_model_name)
        
        # Processing configuration
        self.config = {
            'min_chapter_length': 30.0,  # seconds
            'max_chapters': 15,
            'transcription_language': None,  # auto-detect
            'initial_prompt': None
        }
    
    def process_video(
        self,
        video_id: str,
        job_id: str = None,
        progress_callback: Callable = None,
        config_overrides: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a video to generate chapters
        
        Args:
            video_id: ID of the video to process
            job_id: ID of the processing job
            progress_callback: Function to call with progress updates
            config_overrides: Configuration overrides
            
        Returns:
            Dictionary with processing results
        """
        
        try:
            # Get video and job objects
            video = Video.get_by_id(video_id)
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            job = ProcessingJob.get_by_id(job_id) if job_id else None
            
            # Apply configuration overrides
            processing_config = self.config.copy()
            if config_overrides:
                processing_config.update(config_overrides)
            
            logger.info(f"Starting video processing for video {video_id}")
            
            # Step 1: Transcription
            if progress_callback:
                progress_callback(5, "Starting audio transcription")
            
            if job:
                job.update_progress(
                    stage=job.status,
                    progress=5.0,
                    metadata={'step': 'transcription_start'}
                )
            
            transcript_segments = self._transcribe_video(
                video,
                processing_config,
                progress_callback,
                job
            )
            
            # Step 2: Chapter Generation
            if progress_callback:
                progress_callback(60, "Generating chapters with AI")
            
            if job:
                job.update_progress(
                    stage=job.status,
                    progress=60.0,
                    metadata={'step': 'chapter_generation_start'}
                )
            
            chapters = self._generate_chapters(
                transcript_segments,
                video,
                processing_config,
                progress_callback,
                job
            )
            
            # Step 3: Save chapters to database
            if progress_callback:
                progress_callback(90, "Saving chapters to database")
            
            if job:
                job.update_progress(
                    stage=job.status,
                    progress=90.0,
                    metadata={'step': 'saving_chapters'}
                )
            
            saved_chapters = self._save_chapters(
                chapters,
                video_id,
                progress_callback
            )
            
            # Step 4: Finalize processing
            if progress_callback:
                progress_callback(100, "Processing completed")
            
            if job:
                job.mark_complete(len(saved_chapters))
            
            # Prepare results
            result = {
                'success': True,
                'video_id': video_id,
                'job_id': job_id,
                'chapters_generated': len(saved_chapters),
                'chapters': [ch.to_dict() for ch in saved_chapters],
                'transcript_segments': len(transcript_segments),
                'processing_time': datetime.utcnow().isoformat(),
                'config_used': processing_config
            }
            
            logger.info(f"Video processing completed successfully: {len(saved_chapters)} chapters generated")
            return result
            
        except Exception as e:
            logger.error(f"Video processing failed for video {video_id}: {str(e)}")
            
            if job:
                job.mark_error(f"Processing failed: {str(e)}")
            
            if progress_callback:
                progress_callback(0, f"Processing failed: {str(e)}")
            
            raise
    
    def _transcribe_video(
        self,
        video: Video,
        config: Dict[str, Any],
        progress_callback: Callable = None,
        job: ProcessingJob = None
    ) -> List[Dict[str, Any]]:
        """Transcribe video audio to text"""
        
        try:
            # Create progress wrapper for transcription (0-50% range)
            def transcription_progress(progress, message):
                adjusted_progress = (progress / 100) * 50  # Map to 0-50%
                if progress_callback:
                    progress_callback(adjusted_progress, f"Transcription: {message}")
                
                if job:
                    job.update_progress(
                        progress=adjusted_progress,
                        metadata={'step': 'transcription', 'substep': message}
                    )
            
            # Perform transcription
            transcript_segments = self.asr_processor.transcribe_video(
                video_path=video.file_path,
                language=config.get('transcription_language'),
                initial_prompt=config.get('initial_prompt'),
                progress_callback=transcription_progress,
                keep_audio=False
            )
            
            # Get transcript statistics
            transcript_stats = self.asr_processor.get_transcript_statistics(transcript_segments)
            
            logger.info(f"Transcription completed: {transcript_stats}")
            
            if job:
                job.update_progress(
                    progress=50.0,
                    metadata={
                        'step': 'transcription_complete',
                        'transcript_stats': transcript_stats
                    }
                )
            
            return transcript_segments
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _generate_chapters(
        self,
        transcript_segments: List[Dict[str, Any]],
        video: Video,
        config: Dict[str, Any],
        progress_callback: Callable = None,
        job: ProcessingJob = None
    ) -> List[Dict[str, Any]]:
        """Generate chapters from transcript using LLM"""
        
        try:
            # Format transcript for LLM input
            formatted_transcript = self.asr_processor.format_transcript_for_chaptering(
                transcript_segments
            )
            
            # Create progress wrapper for chapter generation (50-85% range)
            def chapter_progress(progress, message):
                adjusted_progress = 50 + (progress / 100) * 35  # Map to 50-85%
                if progress_callback:
                    progress_callback(adjusted_progress, f"Chapter Generation: {message}")
                
                if job:
                    job.update_progress(
                        progress=adjusted_progress,
                        metadata={'step': 'chapter_generation', 'substep': message}
                    )
            
            # Generate chapters
            chapters = self.llm_processor.generate_chapters(
                transcript=formatted_transcript,
                video_duration=video.duration,
                segment_count=len(transcript_segments),
                max_chapters=config.get('max_chapters', 15),
                min_chapter_length=config.get('min_chapter_length', 30.0),
                progress_callback=chapter_progress
            )
            
            # Get generation statistics
            generation_stats = self.llm_processor.get_generation_statistics(chapters)
            
            logger.info(f"Chapter generation completed: {generation_stats}")
            
            if job:
                job.update_progress(
                    progress=85.0,
                    metadata={
                        'step': 'chapter_generation_complete',
                        'generation_stats': generation_stats
                    }
                )
            
            return chapters
            
        except Exception as e:
            logger.error(f"Chapter generation failed: {str(e)}")
            raise
    
    def _save_chapters(
        self,
        chapters: List[Dict[str, Any]],
        video_id: str,
        progress_callback: Callable = None
    ) -> List[Chapter]:
        """Save generated chapters to database"""
        
        try:
            saved_chapters = []
            
            for i, chapter_data in enumerate(chapters):
                # Create chapter object
                chapter = Chapter(
                    video_id=video_id,
                    title=chapter_data['title'],
                    start_time=chapter_data['start_time'],
                    end_time=None,  # End time will be calculated based on next chapter
                    confidence=chapter_data.get('confidence', 0.8),
                    is_ai_generated=True,
                    order=i + 1
                )
                
                # Set end time based on next chapter or video duration
                if i < len(chapters) - 1:
                    chapter.end_time = chapters[i + 1]['start_time']
                
                chapter.save()
                saved_chapters.append(chapter)
                
                # Update progress
                if progress_callback:
                    progress = 90 + ((i + 1) / len(chapters)) * 8  # 90-98%
                    progress_callback(progress, f"Saved chapter {i + 1}/{len(chapters)}")
            
            # Update chapter orders
            for chapter in saved_chapters:
                chapter.update_order()
            
            db.session.commit()
            
            logger.info(f"Saved {len(saved_chapters)} chapters to database")
            return saved_chapters
            
        except Exception as e:
            logger.error(f"Failed to save chapters: {str(e)}")
            db.session.rollback()
            raise
    
    def estimate_processing_time(self, video: Video) -> Dict[str, float]:
        """Estimate processing time for a video"""
        
        # Base estimates (in seconds)
        base_transcription_time = video.duration * 0.3  # ~30% of video duration
        base_chapter_generation_time = 60  # ~1 minute for LLM processing
        base_saving_time = 10  # ~10 seconds for database operations
        
        # Adjust based on device capabilities
        device = self.model_manager.device
        
        if device == "cuda":
            # GPU acceleration
            transcription_multiplier = 0.5
            generation_multiplier = 0.3
        elif device == "mps":
            # Apple Silicon
            transcription_multiplier = 0.7
            generation_multiplier = 0.5
        else:
            # CPU only
            transcription_multiplier = 2.0
            generation_multiplier = 3.0
        
        estimated_times = {
            'transcription': base_transcription_time * transcription_multiplier,
            'chapter_generation': base_chapter_generation_time * generation_multiplier,
            'saving': base_saving_time,
            'total': (
                base_transcription_time * transcription_multiplier +
                base_chapter_generation_time * generation_multiplier +
                base_saving_time
            )
        }
        
        return estimated_times
    
    def get_processing_requirements(self) -> Dict[str, Any]:
        """Get system requirements for processing"""
        
        device = self.model_manager.device
        memory_usage = self.model_manager.get_memory_usage()
        
        return {
            'device': device,
            'memory_usage': memory_usage,
            'ffmpeg_required': True,
            'models_loaded': memory_usage.get('models_loaded', []),
            'estimated_memory_gb': 8 if device == "cuda" else 16,  # Rough estimates
            'recommended_free_storage_gb': 5  # For temporary files and model cache
        }
    
    def cleanup_processing_cache(self):
        """Clean up processing cache and temporary files"""
        
        try:
            # Unload models to free memory
            self.model_manager.unload_all_models()
            
            # Clean up any temporary files
            # This would be implemented based on specific temporary file patterns
            
            logger.info("Processing cache cleaned up")
            
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {str(e)}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update processing configuration"""
        
        # Validate configuration values
        if 'min_chapter_length' in new_config:
            if not isinstance(new_config['min_chapter_length'], (int, float)) or new_config['min_chapter_length'] <= 0:
                raise ValueError("min_chapter_length must be a positive number")
        
        if 'max_chapters' in new_config:
            if not isinstance(new_config['max_chapters'], int) or new_config['max_chapters'] <= 0:
                raise ValueError("max_chapters must be a positive integer")
        
        # Update configuration
        self.config.update(new_config)
        logger.info(f"Configuration updated: {new_config}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current processing configuration"""
        return self.config.copy() 