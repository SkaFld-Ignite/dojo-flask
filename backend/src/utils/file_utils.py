"""
File validation and metadata utilities
"""

import os
import magic
from pathlib import Path
from flask import current_app

def validate_video_file(file):
    """
    Validate uploaded video file
    
    Args:
        file: Flask file object
        
    Returns:
        dict: {'valid': bool, 'error': str}
    """
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 1024 * 1024 * 1024)  # 1GB default
    if file_size > max_size:
        return {
            'valid': False,
            'error': f'File size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed size ({max_size / (1024*1024):.1f} MB)'
        }
    
    # Check file extension
    filename = file.filename.lower()
    allowed_extensions = current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', {'.mp4', '.avi', '.mov', '.mkv', '.webm'})
    
    file_extension = Path(filename).suffix
    if file_extension not in allowed_extensions:
        return {
            'valid': False,
            'error': f'File type {file_extension} not allowed. Supported formats: {", ".join(allowed_extensions)}'
        }
    
    # Check MIME type using python-magic
    try:
        file_data = file.read(1024)  # Read first 1KB for MIME detection
        file.seek(0)  # Reset to beginning
        
        mime_type = magic.from_buffer(file_data, mime=True)
        
        if not mime_type.startswith('video/'):
            return {
                'valid': False,
                'error': f'File is not a valid video file (detected type: {mime_type})'
            }
            
    except Exception as e:
        # If magic fails, we'll allow it but log the error
        current_app.logger.warning(f"MIME type detection failed: {str(e)}")
    
    return {'valid': True, 'error': None}

def get_video_metadata(file_path):
    """
    Extract video metadata using ffmpeg/ffprobe
    
    Args:
        file_path: Path to video file
        
    Returns:
        dict: Video metadata
    """
    
    metadata = {
        'duration': None,
        'width': None,
        'height': None,
        'fps': None,
        'bitrate': None,
        'codec': None
    }
    
    try:
        import ffmpeg
        
        # Use ffprobe to get video information
        probe = ffmpeg.probe(file_path)
        
        # Get video stream info
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if video_stream:
            # Duration
            if 'duration' in video_stream:
                metadata['duration'] = float(video_stream['duration'])
            elif 'duration' in probe.get('format', {}):
                metadata['duration'] = float(probe['format']['duration'])
            
            # Video properties
            metadata['width'] = video_stream.get('width')
            metadata['height'] = video_stream.get('height')
            metadata['codec'] = video_stream.get('codec_name')
            
            # Frame rate
            if 'r_frame_rate' in video_stream:
                fps_str = video_stream['r_frame_rate']
                if '/' in fps_str:
                    num, den = map(int, fps_str.split('/'))
                    if den != 0:
                        metadata['fps'] = round(num / den, 2)
            
            # Bitrate
            if 'bit_rate' in video_stream:
                metadata['bitrate'] = int(video_stream['bit_rate'])
            elif 'bit_rate' in probe.get('format', {}):
                metadata['bitrate'] = int(probe['format']['bit_rate'])
        
        # Additional format info
        format_info = probe.get('format', {})
        if not metadata['duration'] and 'duration' in format_info:
            metadata['duration'] = float(format_info['duration'])
        
    except ImportError:
        current_app.logger.warning("ffmpeg-python not available, using basic metadata")
        
        # Fallback: try to get basic file info
        try:
            file_stat = Path(file_path).stat()
            metadata['file_size'] = file_stat.st_size
        except Exception as e:
            current_app.logger.error(f"Failed to get file metadata: {str(e)}")
    
    except Exception as e:
        current_app.logger.error(f"Failed to extract video metadata: {str(e)}")
    
    return metadata

def get_video_thumbnail(video_path, output_path, timestamp=30):
    """
    Generate video thumbnail at specified timestamp
    
    Args:
        video_path: Path to input video
        output_path: Path for output thumbnail
        timestamp: Time in seconds to capture thumbnail
        
    Returns:
        bool: Success status
    """
    
    try:
        import ffmpeg
        
        # Create thumbnail using ffmpeg
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .output(output_path, vframes=1, format='image2', vcodec='png')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        return True
        
    except ImportError:
        current_app.logger.warning("ffmpeg-python not available for thumbnail generation")
        return False
        
    except Exception as e:
        current_app.logger.error(f"Thumbnail generation failed: {str(e)}")
        return False

def cleanup_old_files(directory, max_age_hours=24):
    """
    Clean up old files from directory
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age in hours before cleanup
        
    Returns:
        int: Number of files cleaned up
    """
    
    import time
    
    directory = Path(directory)
    if not directory.exists():
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    try:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1
                    current_app.logger.info(f"Cleaned up old file: {file_path}")
    
    except Exception as e:
        current_app.logger.error(f"File cleanup error: {str(e)}")
    
    return cleaned_count 