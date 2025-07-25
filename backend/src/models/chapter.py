"""
Chapter model for storing video chapters
"""

from .base import db, BaseModel

class Chapter(BaseModel):
    """Chapter model for storing video chapter information"""
    
    __tablename__ = 'chapters'
    
    # Reference to video
    video_id = db.Column(db.String(36), db.ForeignKey('videos.id'), nullable=False)
    
    # Chapter information
    title = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.Float, nullable=False)  # Start time in seconds
    end_time = db.Column(db.Float, nullable=True)  # End time in seconds (optional)
    
    # AI-generated metadata
    confidence = db.Column(db.Float, nullable=True)  # AI confidence score (0-1)
    is_ai_generated = db.Column(db.Boolean, default=True, nullable=False)
    
    # Chapter order and grouping
    order = db.Column(db.Integer, nullable=False)  # Order within the video
    
    # Additional metadata
    description = db.Column(db.Text, nullable=True)  # Optional chapter description
    keywords = db.Column(db.JSON, nullable=True)  # Associated keywords
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Auto-generate order if not provided
        if 'order' not in kwargs and 'video_id' in kwargs:
            max_order = db.session.query(db.func.max(Chapter.order)).filter_by(
                video_id=kwargs['video_id']
            ).scalar()
            self.order = (max_order or 0) + 1
    
    @property
    def timestamp(self):
        """Get timestamp in HH:MM:SS format"""
        return self.seconds_to_timestamp(self.start_time)
    
    @property
    def duration(self):
        """Get chapter duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def duration_formatted(self):
        """Get formatted duration string"""
        if self.duration:
            return self.seconds_to_timestamp(self.duration)
        return "Unknown"
    
    @staticmethod
    def seconds_to_timestamp(seconds):
        """Convert seconds to HH:MM:SS format"""
        if seconds is None:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def timestamp_to_seconds(timestamp):
        """Convert HH:MM:SS timestamp to seconds"""
        if not timestamp:
            return 0
        
        parts = timestamp.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return int(parts[0])
    
    @classmethod
    def get_by_video(cls, video_id):
        """Get all chapters for a video, ordered by start time"""
        return cls.query.filter_by(video_id=video_id).order_by(cls.start_time).all()
    
    @classmethod
    def get_by_time_range(cls, video_id, start_time, end_time):
        """Get chapters within a time range"""
        return cls.query.filter(
            cls.video_id == video_id,
            cls.start_time >= start_time,
            cls.start_time <= end_time
        ).order_by(cls.start_time).all()
    
    @classmethod
    def get_ai_generated(cls, video_id):
        """Get only AI-generated chapters for a video"""
        return cls.query.filter_by(
            video_id=video_id, 
            is_ai_generated=True
        ).order_by(cls.start_time).all()
    
    @classmethod
    def get_manual(cls, video_id):
        """Get only manually created chapters for a video"""
        return cls.query.filter_by(
            video_id=video_id, 
            is_ai_generated=False
        ).order_by(cls.start_time).all()
    
    def update_order(self):
        """Update chapter order based on start time"""
        chapters = Chapter.query.filter_by(video_id=self.video_id).order_by(Chapter.start_time).all()
        for i, chapter in enumerate(chapters, 1):
            chapter.order = i
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary with additional computed fields"""
        result = super().to_dict()
        result.update({
            'timestamp': self.timestamp,
            'duration': self.duration,
            'duration_formatted': self.duration_formatted,
        })
        return result
    
    def __repr__(self):
        return f'<Chapter "{self.title}" at {self.timestamp}>' 