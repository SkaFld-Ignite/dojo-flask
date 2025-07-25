'use client';

import { useState, useCallback, useMemo } from 'react';
import { Chapter, Video } from '../../types';

interface ChapterTimelineProps {
  video: Video;
  chapters: Chapter[];
  currentTime?: number;
  onTimeChange?: (time: number) => void;
  onChapterSelect?: (chapter: Chapter) => void;
  className?: string;
  showLabels?: boolean;
  showTooltips?: boolean;
}

interface ChapterMarker {
  chapter: Chapter;
  position: number; // percentage from 0-100
  width: number; // percentage width of the chapter
}

const ChapterTimeline: React.FC<ChapterTimelineProps> = ({
  video,
  chapters,
  currentTime = 0,
  onTimeChange,
  onChapterSelect,
  className = '',
  showLabels = true,
  showTooltips = true,
}) => {
  const [hoveredChapter, setHoveredChapter] = useState<Chapter | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Sort chapters by start time and calculate positions
  const chapterMarkers: ChapterMarker[] = useMemo(() => {
    if (!video.duration || chapters.length === 0) return [];

    const sortedChapters = [...chapters].sort((a, b) => a.startTime - b.startTime);
    
    return sortedChapters.map((chapter, index) => {
      const startPercent = (chapter.startTime / video.duration) * 100;
      const endTime = chapter.endTime || 
        (index < sortedChapters.length - 1 ? sortedChapters[index + 1].startTime : video.duration);
      const endPercent = (endTime / video.duration) * 100;
      
      return {
        chapter,
        position: startPercent,
        width: endPercent - startPercent,
      };
    });
  }, [chapters, video.duration]);

  // Calculate current playhead position
  const playheadPosition = useMemo(() => {
    if (!video.duration) return 0;
    return Math.min((currentTime / video.duration) * 100, 100);
  }, [currentTime, video.duration]);

  // Find current chapter
  const currentChapter = useMemo(() => {
    return chapters.find(chapter => {
      const endTime = chapter.endTime || video.duration;
      return currentTime >= chapter.startTime && currentTime < endTime;
    });
  }, [currentTime, chapters, video.duration]);

  // Handle timeline click
  const handleTimelineClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!onTimeChange || !video.duration) return;

    const rect = event.currentTarget.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = (clickX / rect.width) * 100;
    const newTime = (percentage / 100) * video.duration;
    
    onTimeChange(Math.max(0, Math.min(newTime, video.duration)));
  }, [onTimeChange, video.duration]);

  // Handle chapter marker click
  const handleChapterClick = useCallback((chapter: Chapter, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (onTimeChange) {
      onTimeChange(chapter.startTime);
    }
    
    if (onChapterSelect) {
      onChapterSelect(chapter);
    }
  }, [onTimeChange, onChapterSelect]);

  // Handle chapter marker hover
  const handleChapterHover = useCallback((chapter: Chapter, event: React.MouseEvent) => {
    if (!showTooltips) return;
    
    setHoveredChapter(chapter);
    setTooltipPosition({
      x: event.clientX,
      y: event.clientY - 10,
    });
  }, [showTooltips]);

  // Format time display
  const formatTime = useCallback((seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Get chapter color based on confidence or type
  const getChapterColor = useCallback((chapter: Chapter) => {
    if (chapter.isAiGenerated) {
      const confidence = chapter.confidence || 0;
      if (confidence >= 0.8) return 'bg-blue-500';
      if (confidence >= 0.6) return 'bg-blue-400';
      return 'bg-blue-300';
    }
    return 'bg-green-500'; // Manual chapters
  }, []);

  if (!video.duration || chapters.length === 0) {
    return (
      <div className={`w-full p-4 text-center text-gray-500 ${className}`}>
        <p>No chapters available for this video</p>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {/* Timeline Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-gray-900">
          Video Chapters ({chapters.length})
        </h3>
        <div className="text-sm text-gray-600">
          {formatTime(currentTime)} / {formatTime(video.duration)}
        </div>
      </div>

      {/* Current Chapter Info */}
      {currentChapter && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-blue-900">{currentChapter.title}</h4>
              <p className="text-sm text-blue-700">
                {formatTime(currentChapter.startTime)} - {formatTime(currentChapter.endTime || video.duration)}
              </p>
            </div>
            {currentChapter.confidence && (
              <div className="text-xs text-blue-600">
                Confidence: {Math.round(currentChapter.confidence * 100)}%
              </div>
            )}
          </div>
          {currentChapter.description && (
            <p className="mt-2 text-sm text-blue-800">{currentChapter.description}</p>
          )}
        </div>
      )}

      {/* Timeline Container */}
      <div className="relative">
        {/* Timeline Bar */}
        <div
          className="relative h-12 bg-gray-200 rounded-lg cursor-pointer overflow-hidden"
          onClick={handleTimelineClick}
        >
          {/* Chapter Segments */}
          {chapterMarkers.map((marker, index) => (
            <div
              key={marker.chapter.id}
              className={`absolute top-0 h-full transition-all duration-200 hover:opacity-80 cursor-pointer border-r border-white ${getChapterColor(marker.chapter)}`}
              style={{
                left: `${marker.position}%`,
                width: `${marker.width}%`,
              }}
              onClick={(e) => handleChapterClick(marker.chapter, e)}
              onMouseEnter={(e) => handleChapterHover(marker.chapter, e)}
              onMouseLeave={() => setHoveredChapter(null)}
              title={marker.chapter.title}
            >
              {/* Chapter Label */}
              {showLabels && marker.width > 10 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-medium text-white truncate px-1">
                    {marker.chapter.title}
                  </span>
                </div>
              )}
            </div>
          ))}

          {/* Playhead */}
          <div
            className="absolute top-0 h-full w-1 bg-red-500 z-10 transition-all duration-100"
            style={{ left: `${playheadPosition}%` }}
          >
            <div className="absolute -top-1 -left-1 w-3 h-3 bg-red-500 rounded-full"></div>
          </div>
        </div>

        {/* Time Markers */}
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>0:00</span>
          {video.duration > 300 && ( // Show middle marker for videos > 5 minutes
            <span>{formatTime(video.duration / 2)}</span>
          )}
          <span>{formatTime(video.duration)}</span>
        </div>
      </div>

      {/* Chapter List */}
      {showLabels && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">All Chapters</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {chapters
              .sort((a, b) => a.startTime - b.startTime)
              .map((chapter) => (
                <div
                  key={chapter.id}
                  className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${
                    currentChapter?.id === chapter.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => handleChapterClick(chapter, {} as React.MouseEvent)}
                >
                  <div className="flex-1 min-w-0">
                    <h5 className="font-medium text-gray-900 truncate">
                      {chapter.title}
                    </h5>
                    <p className="text-sm text-gray-500">
                      {formatTime(chapter.startTime)}
                      {chapter.confidence && (
                        <span className="ml-2">
                          • {Math.round(chapter.confidence * 100)}% confidence
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex-shrink-0 ml-2">
                    <span className={`inline-block w-3 h-3 rounded-full ${getChapterColor(chapter)}`}></span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Tooltip */}
      {hoveredChapter && showTooltips && (
        <div
          className="fixed z-50 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-lg max-w-xs pointer-events-none"
          style={{
            left: tooltipPosition.x - 150,
            top: tooltipPosition.y - 80,
          }}
        >
          <h5 className="font-medium">{hoveredChapter.title}</h5>
          <p className="text-gray-300">
            {formatTime(hoveredChapter.startTime)} - {formatTime(hoveredChapter.endTime || video.duration)}
          </p>
          {hoveredChapter.confidence && (
            <p className="text-gray-300 text-xs mt-1">
              Confidence: {Math.round(hoveredChapter.confidence * 100)}%
            </p>
          )}
          {hoveredChapter.description && (
            <p className="text-gray-300 text-xs mt-1 line-clamp-2">
              {hoveredChapter.description}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default ChapterTimeline; 