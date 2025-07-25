"""
ASR (Automatic Speech Recognition) processor using faster-whisper
"""

import os
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import subprocess

from .model_manager import ModelManager

logger = logging.getLogger(__name__)

class ASRProcessor:
    """Handles audio transcription using faster-whisper"""
    
    def __init__(self, model_size: str = "large-v3"):
        self.model_manager = ModelManager()
        self.model_size = model_size
        self._model_info = None
    
    def _get_model(self) -> Dict[str, Any]:
        """Get or load the ASR model"""
        if self._model_info is None:
            self._model_info = self.model_manager.get_asr_model(self.model_size)
        return self._model_info
    
    def extract_audio_from_video(self, video_path: str, audio_path: str = None) -> str:
        """Extract audio from video file using FFmpeg"""
        
        try:
            if audio_path is None:
                # Create temporary audio file
                temp_dir = tempfile.mkdtemp()
                audio_path = os.path.join(temp_dir, "extracted_audio.wav")
            
            # FFmpeg command to extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
                '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                audio_path
            ]
            
            logger.info(f"Extracting audio from {video_path} to {audio_path}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            logger.info("Audio extraction completed successfully")
            return audio_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
        except Exception as e:
            logger.error(f"Audio extraction failed: {str(e)}")
            raise
    
    def transcribe_audio(
        self, 
        audio_path: str,
        language: str = None,
        initial_prompt: str = None,
        progress_callback: callable = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio file and return segments with timestamps
        
        Args:
            audio_path: Path to audio file
            language: Language code (auto-detect if None)
            initial_prompt: Initial prompt to guide transcription
            progress_callback: Function to call with progress updates
            
        Returns:
            List of transcription segments with timestamps and text
        """
        
        try:
            model_info = self._get_model()
            model = model_info['model']
            
            logger.info(f"Starting transcription of {audio_path}")
            
            # Configure transcription parameters
            transcribe_kwargs = {
                'language': language,
                'initial_prompt': initial_prompt,
                'word_timestamps': True,  # Enable word-level timestamps
                'vad_filter': True,      # Enable voice activity detection
                'vad_parameters': {
                    'min_silence_duration_ms': 500,
                    'speech_pad_ms': 400
                }
            }
            
            # Remove None values
            transcribe_kwargs = {k: v for k, v in transcribe_kwargs.items() if v is not None}
            
            # Perform transcription
            segments_generator, info = model.transcribe(audio_path, **transcribe_kwargs)
            
            # Convert generator to list and process segments
            segments = []
            total_duration = info.duration
            
            logger.info(f"Transcription info - Language: {info.language}, Duration: {total_duration:.2f}s")
            
            for i, segment in enumerate(segments_generator):
                segment_data = {
                    'id': segment.id,
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip(),
                    'words': []
                }
                
                # Add word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        word_data = {
                            'word': word.word,
                            'start': word.start,
                            'end': word.end,
                            'probability': word.probability
                        }
                        segment_data['words'].append(word_data)
                
                segments.append(segment_data)
                
                # Call progress callback if provided
                if progress_callback:
                    progress = (segment.end / total_duration) * 100
                    progress_callback(progress, f"Transcribed {i+1} segments")
            
            logger.info(f"Transcription completed: {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def transcribe_video(
        self,
        video_path: str,
        language: str = None,
        initial_prompt: str = None,
        progress_callback: callable = None,
        keep_audio: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Transcribe video file (extracts audio first)
        
        Args:
            video_path: Path to video file
            language: Language code (auto-detect if None)
            initial_prompt: Initial prompt to guide transcription
            progress_callback: Function to call with progress updates
            keep_audio: Whether to keep extracted audio file
            
        Returns:
            List of transcription segments with timestamps and text
        """
        
        audio_path = None
        try:
            # Update progress
            if progress_callback:
                progress_callback(10, "Extracting audio from video")
            
            # Extract audio from video
            audio_path = self.extract_audio_from_video(video_path)
            
            # Update progress
            if progress_callback:
                progress_callback(20, "Starting transcription")
            
            # Create wrapper for progress callback to account for audio extraction
            def transcribe_progress_callback(progress, message):
                # Map transcription progress to 20-100%
                adjusted_progress = 20 + (progress * 0.8)
                if progress_callback:
                    progress_callback(adjusted_progress, message)
            
            # Transcribe audio
            segments = self.transcribe_audio(
                audio_path,
                language=language,
                initial_prompt=initial_prompt,
                progress_callback=transcribe_progress_callback
            )
            
            # Final progress update
            if progress_callback:
                progress_callback(100, "Transcription completed")
            
            return segments
            
        except Exception as e:
            logger.error(f"Video transcription failed: {str(e)}")
            raise
        finally:
            # Clean up temporary audio file if not keeping it
            if audio_path and not keep_audio and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    # Also remove temporary directory if empty
                    temp_dir = os.path.dirname(audio_path)
                    if temp_dir.startswith(tempfile.gettempdir()):
                        try:
                            os.rmdir(temp_dir)
                        except OSError:
                            pass  # Directory not empty or other issue
                except Exception as e:
                    logger.warning(f"Failed to clean up audio file {audio_path}: {str(e)}")
    
    def format_transcript_for_chaptering(self, segments: List[Dict[str, Any]]) -> str:
        """
        Format transcript segments for LLM chaptering input
        
        Args:
            segments: List of transcript segments
            
        Returns:
            Formatted transcript text with timestamps
        """
        
        formatted_lines = []
        
        for segment in segments:
            start_time = self._format_timestamp(segment['start'])
            text = segment['text'].strip()
            
            if text:  # Only include non-empty segments
                formatted_lines.append(f"[{start_time}] {text}")
        
        return "\n".join(formatted_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_transcript_statistics(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the transcript"""
        
        if not segments:
            return {}
        
        total_duration = max(segment['end'] for segment in segments)
        total_words = sum(len(segment.get('words', [])) for segment in segments)
        total_text_length = sum(len(segment['text']) for segment in segments)
        
        # Calculate speaking rate (words per minute)
        speaking_rate = (total_words / total_duration) * 60 if total_duration > 0 else 0
        
        return {
            'total_segments': len(segments),
            'total_duration': total_duration,
            'total_words': total_words,
            'total_characters': total_text_length,
            'speaking_rate_wpm': round(speaking_rate, 1),
            'average_segment_length': round(total_duration / len(segments), 2) if segments else 0
        } 