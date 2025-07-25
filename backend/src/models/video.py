"""
Video model for storing video file information
"""

from sqlalchemy import func
from .base import db, BaseModel

class Video(BaseModel):
    """Video model for storing uploaded video information"""
    
    __tablename__ = 'videos'
    
    # Basic file information
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.BigInteger, nullable=False)  # Size in bytes
    duration = db.Column(db.Float, nullable=True)  # Duration in seconds
    format = db.Column(db.String(10), nullable=False)  # File extension
    mime_type = db.Column(db.String(50), nullable=False)
    
    # Storage information
    path = db.Column(db.String(500), nullable=False)  # Relative path to file
    
    # Processing status
    processing_status = db.Column(
        db.Enum('pending', 'processing', 'completed', 'failed', name='processing_status'),
        default='pending',
        nullable=False
    )
    
    # Metadata
    thumbnail_path = db.Column(db.String(500), nullable=True)
    video_metadata = db.Column(db.JSON, nullable=True)  # Store additional video metadata
    
    # Relationships
    chapters = db.relationship('Chapter', backref='video', cascade='all, delete-orphan')
    processing_jobs = db.relationship('ProcessingJob', backref='video', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @classmethod
    def get_by_filename(cls, filename):
        """Get video by filename"""
        return cls.query.filter_by(filename=filename).first()
    
    @classmethod
    def get_recent(cls, limit=10):
        """Get recently uploaded videos"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_by_status(cls, status):
        """Get videos by processing status"""
        return cls.query.filter_by(processing_status=status).all()
    
    def get_chapters_count(self):
        """Get number of chapters for this video"""
        return len(self.chapters)
    
    def get_duration_formatted(self):
        """Get formatted duration string (HH:MM:SS)"""
        if not self.duration:
            return "Unknown"
        
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_size_formatted(self):
        """Get formatted file size string"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.1f} GB"
    
    def to_dict(self):
        """Convert to dictionary with additional computed fields"""
        result = super().to_dict()
        result.update({
            'chapters_count': self.get_chapters_count(),
            'duration_formatted': self.get_duration_formatted(),
            'size_formatted': self.get_size_formatted(),
        })
        return result
    
    def __repr__(self):
        return f'<Video {self.filename} ({self.processing_status})>' 