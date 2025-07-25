"""
LLM processor for generating video chapters using Llama model
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import torch

from .model_manager import ModelManager

logger = logging.getLogger(__name__)

class LLMProcessor:
    """Handles chapter generation using Llama LLM"""
    
    def __init__(self, model_name: str = "meta-llama/Llama-3.1-8B-Instruct"):
        self.model_manager = ModelManager()
        self.model_name = model_name
        self._model_info = None
        
        # Chapter generation prompts
        self.system_prompt = self._get_system_prompt()
        self.chapter_prompt_template = self._get_chapter_prompt_template()
    
    def _get_model(self) -> Dict[str, Any]:
        """Get or load the LLM model"""
        if self._model_info is None:
            self._model_info = self.model_manager.get_llm_model(self.model_name)
        return self._model_info
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for chapter generation"""
        return """You are an expert video content analyzer specializing in creating meaningful chapter divisions for videos based on transcripts. Your task is to analyze video transcripts and generate logical chapter breaks with descriptive titles.

Guidelines:
1. Create chapters that represent meaningful content shifts or topics
2. Ensure chapters are not too short (minimum 30 seconds) or too long (maximum 10 minutes)
3. Use clear, descriptive titles that accurately represent the content
4. Consider natural speech patterns and pauses when determining breaks
5. Aim for 3-15 chapters depending on video length
6. Respond ONLY with valid JSON format

Output format:
{
  "chapters": [
    {
      "start_time": 0,
      "title": "Chapter Title",
      "confidence": 0.95
    }
  ]
}"""
    
    def _get_chapter_prompt_template(self) -> str:
        """Get the prompt template for chapter generation"""
        return """Analyze the following video transcript and create logical chapter divisions. The transcript includes timestamps in [HH:MM:SS] format.

Video Information:
- Duration: {duration} seconds ({duration_formatted})
- Total segments: {segment_count}

Transcript:
{transcript}

Please create meaningful chapters for this video. Consider content flow, topic changes, and natural breaks. Respond with JSON format only."""
    
    def generate_chapters(
        self,
        transcript: str,
        video_duration: float,
        segment_count: int,
        max_chapters: int = 15,
        min_chapter_length: float = 30.0,
        progress_callback: callable = None
    ) -> List[Dict[str, Any]]:
        """
        Generate chapters from transcript using LLM
        
        Args:
            transcript: Formatted transcript with timestamps
            video_duration: Total video duration in seconds
            segment_count: Number of transcript segments
            max_chapters: Maximum number of chapters to generate
            min_chapter_length: Minimum chapter length in seconds
            progress_callback: Function to call with progress updates
            
        Returns:
            List of chapter dictionaries with start_time, title, and confidence
        """
        
        try:
            if progress_callback:
                progress_callback(10, "Loading language model")
            
            model_info = self._get_model()
            model = model_info['model']
            tokenizer = model_info['tokenizer']
            device = model_info['device']
            
            if progress_callback:
                progress_callback(30, "Preparing chapter generation prompt")
            
            # Format duration for display
            duration_formatted = self._format_duration(video_duration)
            
            # Create the full prompt
            user_prompt = self.chapter_prompt_template.format(
                duration=int(video_duration),
                duration_formatted=duration_formatted,
                segment_count=segment_count,
                transcript=transcript
            )
            
            if progress_callback:
                progress_callback(50, "Generating chapters with AI model")
            
            # Generate chapters
            chapters = self._generate_with_retry(
                model, tokenizer, device, user_prompt, max_chapters, min_chapter_length
            )
            
            if progress_callback:
                progress_callback(80, "Processing generated chapters")
            
            # Validate and process chapters
            validated_chapters = self._validate_and_process_chapters(
                chapters, video_duration, min_chapter_length
            )
            
            if progress_callback:
                progress_callback(100, f"Generated {len(validated_chapters)} chapters")
            
            logger.info(f"Successfully generated {len(validated_chapters)} chapters")
            return validated_chapters
            
        except Exception as e:
            logger.error(f"Chapter generation failed: {str(e)}")
            raise
    
    def _generate_with_retry(
        self,
        model,
        tokenizer,
        device: str,
        user_prompt: str,
        max_chapters: int,
        min_chapter_length: float,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate chapters with retry logic for better results"""
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Chapter generation attempt {attempt + 1}")
                
                # Create messages for chat format
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                # Apply chat template
                prompt = tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
                
                # Tokenize input
                inputs = tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=4096  # Limit context length
                ).to(device)
                
                # Generate response
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=1024,
                        temperature=0.3,  # Lower temperature for more consistent output
                        top_p=0.9,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                
                # Decode response
                response = tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:], 
                    skip_special_tokens=True
                )
                
                # Parse JSON response
                chapters = self._parse_chapter_response(response)
                
                if chapters:
                    logger.info(f"Successfully parsed {len(chapters)} chapters on attempt {attempt + 1}")
                    return chapters
                else:
                    logger.warning(f"No valid chapters parsed on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
        
        # If all retries failed, return fallback chapters
        logger.warning("All generation attempts failed, creating fallback chapters")
        return self._create_fallback_chapters(max_chapters, min_chapter_length)
    
    def _parse_chapter_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract chapter information"""
        
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                if 'chapters' in data and isinstance(data['chapters'], list):
                    chapters = []
                    for chapter in data['chapters']:
                        if self._is_valid_chapter(chapter):
                            chapters.append({
                                'start_time': float(chapter['start_time']),
                                'title': str(chapter['title']).strip(),
                                'confidence': float(chapter.get('confidence', 0.8))
                            })
                    return chapters
            
            # Fallback: try to parse line by line
            return self._parse_fallback_format(response)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {str(e)}")
            return self._parse_fallback_format(response)
        except Exception as e:
            logger.error(f"Chapter parsing failed: {str(e)}")
            return []
    
    def _parse_fallback_format(self, response: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON responses"""
        
        chapters = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for patterns like "00:00 - Chapter Title" or "0:00 Chapter Title"
            time_patterns = [
                r'(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*(.+)',
                r'(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)',
                r'Chapter\s+\d+:\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*(.+)'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    time_str = match.group(1)
                    title = match.group(2).strip()
                    
                    if title and len(title) > 3:  # Minimum title length
                        start_time = self._parse_timestamp(time_str)
                        if start_time is not None:
                            chapters.append({
                                'start_time': start_time,
                                'title': title,
                                'confidence': 0.7  # Lower confidence for fallback parsing
                            })
                    break
        
        return chapters
    
    def _parse_timestamp(self, time_str: str) -> Optional[float]:
        """Parse timestamp string to seconds"""
        
        try:
            parts = time_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            pass
        
        return None
    
    def _is_valid_chapter(self, chapter: Dict[str, Any]) -> bool:
        """Validate chapter data structure"""
        
        required_fields = ['start_time', 'title']
        return (
            isinstance(chapter, dict) and
            all(field in chapter for field in required_fields) and
            isinstance(chapter['start_time'], (int, float)) and
            isinstance(chapter['title'], str) and
            len(chapter['title'].strip()) > 0
        )
    
    def _validate_and_process_chapters(
        self,
        chapters: List[Dict[str, Any]],
        video_duration: float,
        min_chapter_length: float
    ) -> List[Dict[str, Any]]:
        """Validate and process generated chapters"""
        
        if not chapters:
            return self._create_fallback_chapters(5, min_chapter_length)
        
        # Sort chapters by start time
        chapters = sorted(chapters, key=lambda x: x['start_time'])
        
        # Ensure first chapter starts at 0
        if chapters[0]['start_time'] > 0:
            chapters.insert(0, {
                'start_time': 0,
                'title': 'Introduction',
                'confidence': 0.8
            })
        
        # Remove chapters that start beyond video duration
        chapters = [ch for ch in chapters if ch['start_time'] < video_duration]
        
        # Merge chapters that are too close together
        filtered_chapters = []
        for i, chapter in enumerate(chapters):
            if i == 0:
                filtered_chapters.append(chapter)
            else:
                time_diff = chapter['start_time'] - filtered_chapters[-1]['start_time']
                if time_diff >= min_chapter_length:
                    filtered_chapters.append(chapter)
                else:
                    # Merge with previous chapter (keep the one with higher confidence)
                    if chapter.get('confidence', 0) > filtered_chapters[-1].get('confidence', 0):
                        filtered_chapters[-1] = chapter
        
        # Ensure we have reasonable number of chapters
        if len(filtered_chapters) > 15:
            # Keep chapters with highest confidence
            filtered_chapters = sorted(filtered_chapters, key=lambda x: x.get('confidence', 0), reverse=True)[:15]
            filtered_chapters = sorted(filtered_chapters, key=lambda x: x['start_time'])
        
        return filtered_chapters
    
    def _create_fallback_chapters(self, num_chapters: int, min_chapter_length: float) -> List[Dict[str, Any]]:
        """Create fallback chapters when LLM generation fails"""
        
        logger.info("Creating fallback chapters")
        
        chapters = []
        for i in range(num_chapters):
            start_time = i * min_chapter_length
            chapters.append({
                'start_time': start_time,
                'title': f'Chapter {i + 1}',
                'confidence': 0.5  # Low confidence for fallback
            })
        
        return chapters
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def get_generation_statistics(self, chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about generated chapters"""
        
        if not chapters:
            return {}
        
        confidences = [ch.get('confidence', 0) for ch in chapters]
        
        return {
            'total_chapters': len(chapters),
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'min_confidence': min(confidences) if confidences else 0,
            'max_confidence': max(confidences) if confidences else 0,
            'high_confidence_chapters': len([c for c in confidences if c >= 0.8]),
            'low_confidence_chapters': len([c for c in confidences if c < 0.6])
        } 