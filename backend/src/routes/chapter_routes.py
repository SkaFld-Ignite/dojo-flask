"""
Chapter management API routes
"""

from flask import Blueprint, request, jsonify, current_app
from ..models import Chapter, Video, db
from ..utils.response_utils import success_response, error_response, validation_error_response

chapter_bp = Blueprint('chapters', __name__)

@chapter_bp.route('/', methods=['POST'])
def create_chapter():
    """Create a new chapter"""
    
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)
    
    # Validate required fields
    required_fields = ['videoId', 'title', 'startTime']
    validation_errors = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            validation_errors.append(f'{field} is required')
    
    if validation_errors:
        return validation_error_response(validation_errors)
    
    # Validate video exists
    video = Video.get_by_id(data['videoId'])
    if not video:
        return error_response('Video not found', 404)
    
    # Validate time values
    start_time = data['startTime']
    end_time = data.get('endTime')
    
    if not isinstance(start_time, (int, float)) or start_time < 0:
        return error_response('startTime must be a positive number', 400)
    
    if end_time is not None:
        if not isinstance(end_time, (int, float)) or end_time <= start_time:
            return error_response('endTime must be greater than startTime', 400)
    
    try:
        # Create chapter
        chapter = Chapter(
            video_id=data['videoId'],
            title=data['title'],
            start_time=start_time,
            end_time=end_time,
            confidence=data.get('confidence'),
            is_ai_generated=data.get('isAiGenerated', False),
            description=data.get('description'),
            keywords=data.get('keywords')
        )
        chapter.save()
        
        # Update chapter orders
        chapter.update_order()
        
        return success_response({
            'chapter': chapter.to_dict()
        }, message='Chapter created successfully', status_code=201)
        
    except Exception as e:
        current_app.logger.error(f"Chapter creation error: {str(e)}")
        return error_response('Failed to create chapter', 500)

@chapter_bp.route('/<chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    """Get chapter by ID"""
    
    chapter = Chapter.get_by_id(chapter_id)
    if not chapter:
        return error_response('Chapter not found', 404)
    
    return success_response({
        'chapter': chapter.to_dict()
    })

@chapter_bp.route('/video/<video_id>', methods=['GET'])
def get_chapters_by_video(video_id):
    """Get all chapters for a video"""
    
    # Validate video exists
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    # Get query parameters
    ai_only = request.args.get('aiOnly', '').lower() == 'true'
    manual_only = request.args.get('manualOnly', '').lower() == 'true'
    
    # Get chapters based on filters
    if ai_only:
        chapters = Chapter.get_ai_generated(video_id)
    elif manual_only:
        chapters = Chapter.get_manual(video_id)
    else:
        chapters = Chapter.get_by_video(video_id)
    
    chapters_data = [chapter.to_dict() for chapter in chapters]
    
    return success_response({
        'chapters': chapters_data,
        'video': video.to_dict(),
        'totalChapters': len(chapters_data)
    })

@chapter_bp.route('/<chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    """Update chapter"""
    
    chapter = Chapter.get_by_id(chapter_id)
    if not chapter:
        return error_response('Chapter not found', 404)
    
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)
    
    # Validate updatable fields
    updatable_fields = ['title', 'startTime', 'endTime', 'description', 'keywords']
    validation_errors = []
    
    try:
        # Update allowed fields
        for field in updatable_fields:
            if field in data:
                if field == 'startTime':
                    start_time = data[field]
                    if not isinstance(start_time, (int, float)) or start_time < 0:
                        validation_errors.append('startTime must be a positive number')
                    else:
                        chapter.start_time = start_time
                
                elif field == 'endTime':
                    end_time = data[field]
                    if end_time is not None:
                        if not isinstance(end_time, (int, float)) or end_time <= chapter.start_time:
                            validation_errors.append('endTime must be greater than startTime')
                        else:
                            chapter.end_time = end_time
                    else:
                        chapter.end_time = None
                
                elif field == 'title':
                    if not data[field] or not isinstance(data[field], str):
                        validation_errors.append('title must be a non-empty string')
                    else:
                        chapter.title = data[field]
                
                else:
                    setattr(chapter, field, data[field])
        
        if validation_errors:
            return validation_error_response(validation_errors)
        
        chapter.save()
        
        # Update chapter orders if times changed
        if 'startTime' in data or 'endTime' in data:
            chapter.update_order()
        
        return success_response({
            'chapter': chapter.to_dict()
        }, message='Chapter updated successfully')
        
    except Exception as e:
        current_app.logger.error(f"Chapter update error: {str(e)}")
        return error_response('Failed to update chapter', 500)

@chapter_bp.route('/<chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    """Delete chapter"""
    
    chapter = Chapter.get_by_id(chapter_id)
    if not chapter:
        return error_response('Chapter not found', 404)
    
    try:
        video_id = chapter.video_id
        chapter.delete()
        
        # Update remaining chapter orders
        remaining_chapters = Chapter.get_by_video(video_id)
        for i, remaining_chapter in enumerate(remaining_chapters, 1):
            remaining_chapter.order = i
        db.session.commit()
        
        return success_response(message='Chapter deleted successfully')
        
    except Exception as e:
        current_app.logger.error(f"Chapter deletion error: {str(e)}")
        return error_response('Failed to delete chapter', 500)

@chapter_bp.route('/video/<video_id>/export', methods=['POST'])
def export_chapters(video_id):
    """Export chapters in various formats"""
    
    # Validate video exists
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    data = request.get_json()
    if not data:
        return error_response('No export options provided', 400)
    
    export_format = data.get('format', 'json').lower()
    include_timestamps = data.get('includeTimestamps', True)
    include_confidence = data.get('includeConfidence', True)
    chapter_ids = data.get('chapterIds')  # Optional: export specific chapters
    
    # Get chapters
    if chapter_ids:
        chapters = [Chapter.get_by_id(cid) for cid in chapter_ids if Chapter.get_by_id(cid)]
        chapters = [c for c in chapters if c.video_id == video_id]  # Security check
    else:
        chapters = Chapter.get_by_video(video_id)
    
    if not chapters:
        return error_response('No chapters found for export', 404)
    
    try:
        exported_data = export_chapters_format(chapters, export_format, include_timestamps, include_confidence)
        
        return success_response({
            'exportData': exported_data,
            'format': export_format,
            'totalChapters': len(chapters),
            'filename': f"{video.original_name}_chapters.{export_format}"
        }, message='Chapters exported successfully')
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Chapter export error: {str(e)}")
        return error_response('Export failed', 500)

@chapter_bp.route('/video/<video_id>/reorder', methods=['POST'])
def reorder_chapters(video_id):
    """Reorder chapters for a video"""
    
    # Validate video exists
    video = Video.get_by_id(video_id)
    if not video:
        return error_response('Video not found', 404)
    
    data = request.get_json()
    if not data or 'chapterIds' not in data:
        return error_response('Chapter IDs array required', 400)
    
    chapter_ids = data['chapterIds']
    if not isinstance(chapter_ids, list):
        return error_response('chapterIds must be an array', 400)
    
    try:
        # Validate all chapters exist and belong to the video
        chapters = []
        for chapter_id in chapter_ids:
            chapter = Chapter.get_by_id(chapter_id)
            if not chapter:
                return error_response(f'Chapter {chapter_id} not found', 404)
            if chapter.video_id != video_id:
                return error_response(f'Chapter {chapter_id} does not belong to this video', 400)
            chapters.append(chapter)
        
        # Update order based on array position
        for i, chapter in enumerate(chapters, 1):
            chapter.order = i
        
        db.session.commit()
        
        # Return updated chapters
        updated_chapters = Chapter.get_by_video(video_id)
        chapters_data = [chapter.to_dict() for chapter in updated_chapters]
        
        return success_response({
            'chapters': chapters_data
        }, message='Chapters reordered successfully')
        
    except Exception as e:
        current_app.logger.error(f"Chapter reorder error: {str(e)}")
        return error_response('Failed to reorder chapters', 500)

def export_chapters_format(chapters, format_type, include_timestamps=True, include_confidence=True):
    """Export chapters in specified format"""
    
    if format_type == 'json':
        return [chapter.to_dict() for chapter in chapters]
    
    elif format_type == 'srt':
        # SubRip subtitle format
        srt_content = []
        for i, chapter in enumerate(chapters, 1):
            start_time = format_srt_time(chapter.start_time)
            end_time = format_srt_time(chapter.end_time or (chapter.start_time + 60))
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(chapter.title)
            srt_content.append("")  # Empty line between entries
        
        return "\n".join(srt_content)
    
    elif format_type == 'vtt':
        # WebVTT format
        vtt_content = ["WEBVTT", ""]
        
        for chapter in chapters:
            start_time = format_vtt_time(chapter.start_time)
            end_time = format_vtt_time(chapter.end_time or (chapter.start_time + 60))
            
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(chapter.title)
            vtt_content.append("")  # Empty line between entries
        
        return "\n".join(vtt_content)
    
    elif format_type == 'csv':
        # CSV format
        csv_lines = []
        headers = ['Title', 'Start Time', 'End Time']
        if include_timestamps:
            headers.extend(['Start Timestamp', 'End Timestamp'])
        if include_confidence:
            headers.append('Confidence')
        
        csv_lines.append(','.join(headers))
        
        for chapter in chapters:
            row = [
                f'"{chapter.title}"',
                str(chapter.start_time),
                str(chapter.end_time or '')
            ]
            
            if include_timestamps:
                row.extend([
                    f'"{chapter.timestamp}"',
                    f'"{chapter.seconds_to_timestamp(chapter.end_time) if chapter.end_time else ""}"'
                ])
            
            if include_confidence:
                row.append(str(chapter.confidence or ''))
            
            csv_lines.append(','.join(row))
        
        return '\n'.join(csv_lines)
    
    elif format_type == 'txt':
        # Plain text format
        txt_lines = []
        for chapter in chapters:
            line = f"{chapter.timestamp} - {chapter.title}"
            if include_confidence and chapter.confidence:
                line += f" (Confidence: {chapter.confidence:.2f})"
            txt_lines.append(line)
        
        return '\n'.join(txt_lines)
    
    else:
        raise ValueError(f"Unsupported export format: {format_type}")

def format_srt_time(seconds):
    """Format time for SRT subtitle format (HH:MM:SS,mmm)"""
    if seconds is None:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def format_vtt_time(seconds):
    """Format time for WebVTT format (HH:MM:SS.mmm)"""
    if seconds is None:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}" 