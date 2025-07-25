"""
ProcessingJob model for tracking video processing tasks
"""

from enum import Enum
from .base import db, BaseModel

class ProcessingStage(Enum):
    """Processing stages enum"""
    UPLOADING = 'uploading'
    EXTRACTING_AUDIO = 'extracting_audio'
    GENERATING_TRANSCRIPT = 'generating_transcript'
    ANALYZING_CONTENT = 'analyzing_content'
    GENERATING_CHAPTERS = 'generating_chapters'
    FINALIZING = 'finalizing'
    COMPLETE = 'complete'
    ERROR = 'error'

class ProcessingJob(BaseModel):
    """ProcessingJob model for tracking video processing tasks"""
    
    __tablename__ = 'processing_jobs'
    
    # Reference to video
    video_id = db.Column(db.String(36), db.ForeignKey('videos.id'), nullable=False)
    
    # Job status and progress
    status = db.Column(
        db.Enum(ProcessingStage, name='processing_stage'),
        default=ProcessingStage.UPLOADING,
        nullable=False
    )
    progress = db.Column(db.Float, default=0.0, nullable=False)  # 0-100
    
    # Timing information
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    estimated_time_remaining = db.Column(db.Integer, nullable=True)  # seconds
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.JSON, nullable=True)
    
    # Stage-specific progress
    stage_progress = db.Column(db.JSON, nullable=True)  # Progress per stage
    
    # Processing metadata
    metadata = db.Column(db.JSON, nullable=True)  # Store processing-specific data
    
    # Configuration
    config = db.Column(db.JSON, nullable=True)  # Store job configuration
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize stage progress
        if not self.stage_progress:
            self.stage_progress = {
                stage.value: 0.0 for stage in ProcessingStage
                if stage not in [ProcessingStage.COMPLETE, ProcessingStage.ERROR]
            }
        
        # Initialize metadata
        if not self.metadata:
            self.metadata = {
                'asr_duration': None,
                'transcript_length': None,
                'chapters_generated': None,
                'llm_inference_time': None,
                'model_used': None,
                'processing_errors': []
            }
    
    @property
    def is_complete(self):
        """Check if job is complete"""
        return self.status in [ProcessingStage.COMPLETE, ProcessingStage.ERROR]
    
    @property
    def is_processing(self):
        """Check if job is currently processing"""
        return self.status not in [
            ProcessingStage.UPLOADING, 
            ProcessingStage.COMPLETE, 
            ProcessingStage.ERROR
        ]
    
    @property
    def time_elapsed(self):
        """Get time elapsed since job start (in seconds)"""
        if not self.start_time:
            return 0
        
        from datetime import datetime
        end_time = self.end_time or datetime.utcnow()
        return (end_time - self.start_time).total_seconds()
    
    @property
    def current_stage_description(self):
        """Get human-readable description of current stage"""
        stage_descriptions = {
            ProcessingStage.UPLOADING: "Uploading video file",
            ProcessingStage.EXTRACTING_AUDIO: "Extracting audio from video",
            ProcessingStage.GENERATING_TRANSCRIPT: "Generating transcript using AI",
            ProcessingStage.ANALYZING_CONTENT: "Analyzing video content",
            ProcessingStage.GENERATING_CHAPTERS: "Generating chapters with AI",
            ProcessingStage.FINALIZING: "Finalizing results",
            ProcessingStage.COMPLETE: "Processing complete",
            ProcessingStage.ERROR: "Processing failed"
        }
        return stage_descriptions.get(self.status, "Unknown stage")
    
    def update_progress(self, stage=None, progress=None, stage_progress=None, metadata=None):
        """Update job progress"""
        if stage:
            self.status = stage
        
        if progress is not None:
            self.progress = min(100.0, max(0.0, progress))
        
        if stage_progress:
            if not self.stage_progress:
                self.stage_progress = {}
            self.stage_progress.update(stage_progress)
        
        if metadata:
            if not self.metadata:
                self.metadata = {}
            self.metadata.update(metadata)
        
        # Mark as complete if progress is 100%
        if self.progress >= 100.0 and self.status != ProcessingStage.ERROR:
            self.status = ProcessingStage.COMPLETE
            if not self.end_time:
                from datetime import datetime
                self.end_time = datetime.utcnow()
    
    def mark_error(self, error_message, error_details=None):
        """Mark job as failed with error details"""
        self.status = ProcessingStage.ERROR
        self.error_message = error_message
        self.error_details = error_details
        
        if not self.end_time:
            from datetime import datetime
            self.end_time = datetime.utcnow()
        
        # Add to processing errors in metadata
        if not self.metadata:
            self.metadata = {}
        if 'processing_errors' not in self.metadata:
            self.metadata['processing_errors'] = []
        
        self.metadata['processing_errors'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'stage': self.status.value,
            'message': error_message,
            'details': error_details
        })
    
    def mark_complete(self, chapters_generated=None):
        """Mark job as complete"""
        self.status = ProcessingStage.COMPLETE
        self.progress = 100.0
        
        if not self.end_time:
            from datetime import datetime
            self.end_time = datetime.utcnow()
        
        if chapters_generated is not None and self.metadata:
            self.metadata['chapters_generated'] = chapters_generated
    
    @classmethod
    def get_active_jobs(cls):
        """Get all active (non-complete) jobs"""
        return cls.query.filter(
            cls.status.notin_([ProcessingStage.COMPLETE, ProcessingStage.ERROR])
        ).all()
    
    @classmethod
    def get_by_video(cls, video_id):
        """Get all jobs for a video"""
        return cls.query.filter_by(video_id=video_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_latest_by_video(cls, video_id):
        """Get the latest job for a video"""
        return cls.query.filter_by(video_id=video_id).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def get_by_status(cls, status):
        """Get jobs by status"""
        return cls.query.filter_by(status=status).all()
    
    def get_progress_percentage(self, stage=None):
        """Get progress percentage for a specific stage or overall"""
        if stage and self.stage_progress:
            return self.stage_progress.get(stage.value, 0.0)
        return self.progress
    
    def estimate_remaining_time(self):
        """Estimate remaining processing time based on current progress"""
        if self.progress <= 0 or not self.start_time:
            return None
        
        time_elapsed = self.time_elapsed
        if time_elapsed <= 0:
            return None
        
        # Calculate estimated total time based on current progress
        estimated_total_time = time_elapsed * (100.0 / self.progress)
        remaining_time = estimated_total_time - time_elapsed
        
        return max(0, int(remaining_time))
    
    def to_dict(self):
        """Convert to dictionary with additional computed fields"""
        result = super().to_dict()
        result.update({
            'status_description': self.current_stage_description,
            'time_elapsed': self.time_elapsed,
            'estimated_time_remaining': self.estimate_remaining_time(),
            'is_complete': self.is_complete,
            'is_processing': self.is_processing,
        })
        return result
    
    def __repr__(self):
        return f'<ProcessingJob {self.id} ({self.status.value}) - {self.progress:.1f}%>' 