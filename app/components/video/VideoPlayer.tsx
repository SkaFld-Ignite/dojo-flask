'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Video, Chapter } from '../../types';
import { ChapterTimeline } from '../timeline';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';

interface VideoPlayerProps {
  video: Video;
  chapters?: Chapter[];
  className?: string;
  autoPlay?: boolean;
  showControls?: boolean;
  showChapterTimeline?: boolean;
  onTimeUpdate?: (currentTime: number) => void;
  onChapterChange?: (chapter: Chapter | null) => void;
  onPlay?: () => void;
  onPause?: () => void;
  onEnded?: () => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  video,
  chapters = [],
  className = '',
  autoPlay = false,
  showControls = true,
  showChapterTimeline = true,
  onTimeUpdate,
  onChapterChange,
  onPlay,
  onPause,
  onEnded,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentChapter, setCurrentChapter] = useState<Chapter | null>(null);

  // Format time for display
  const formatTime = useCallback((seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Update current chapter based on current time
  const updateCurrentChapter = useCallback((time: number) => {
    const chapter = chapters.find(ch => {
      const endTime = ch.endTime || duration;
      return time >= ch.startTime && time < endTime;
    });
    
    if (chapter !== currentChapter) {
      setCurrentChapter(chapter || null);
      onChapterChange?.(chapter || null);
    }
  }, [chapters, duration, currentChapter, onChapterChange]);

  // Video event handlers
  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      setIsLoading(false);
    }
  }, []);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime;
      setCurrentTime(time);
      updateCurrentChapter(time);
      onTimeUpdate?.(time);
    }
  }, [updateCurrentChapter, onTimeUpdate]);

  const handlePlay = useCallback(() => {
    setIsPlaying(true);
    onPlay?.();
  }, [onPlay]);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
    onPause?.();
  }, [onPause]);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    onEnded?.();
  }, [onEnded]);

  const handleError = useCallback(() => {
    setError('Failed to load video');
    setIsLoading(false);
  }, []);

  // Control functions
  const togglePlayPause = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play().catch(console.error);
      }
    }
  }, [isPlaying]);

  const seekToTime = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, Math.min(time, duration));
    }
  }, [duration]);

  const handleVolumeChange = useCallback((newVolume: number) => {
    if (videoRef.current) {
      const volume = Math.max(0, Math.min(1, newVolume));
      videoRef.current.volume = volume;
      setVolume(volume);
      setIsMuted(volume === 0);
    }
  }, []);

  const toggleMute = useCallback(() => {
    if (videoRef.current) {
      const newMuted = !isMuted;
      videoRef.current.muted = newMuted;
      setIsMuted(newMuted);
    }
  }, [isMuted]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen().catch(console.error);
    } else {
      document.exitFullscreen().catch(console.error);
    }
  }, []);

  // Chapter navigation
  const goToChapter = useCallback((chapter: Chapter) => {
    seekToTime(chapter.startTime);
  }, [seekToTime]);

  const goToPreviousChapter = useCallback(() => {
    const sortedChapters = [...chapters].sort((a, b) => a.startTime - b.startTime);
    const currentIndex = sortedChapters.findIndex(ch => ch.id === currentChapter?.id);
    
    if (currentIndex > 0) {
      goToChapter(sortedChapters[currentIndex - 1]);
    } else if (sortedChapters.length > 0) {
      // Go to beginning of current chapter or video
      seekToTime(currentChapter?.startTime || 0);
    }
  }, [chapters, currentChapter, goToChapter, seekToTime]);

  const goToNextChapter = useCallback(() => {
    const sortedChapters = [...chapters].sort((a, b) => a.startTime - b.startTime);
    const currentIndex = sortedChapters.findIndex(ch => ch.id === currentChapter?.id);
    
    if (currentIndex >= 0 && currentIndex < sortedChapters.length - 1) {
      goToChapter(sortedChapters[currentIndex + 1]);
    }
  }, [chapters, currentChapter, goToChapter]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle shortcuts when video player is focused or visible
      if (!videoRef.current) return;

      switch (event.code) {
        case 'Space':
          event.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          event.preventDefault();
          seekToTime(currentTime - 10);
          break;
        case 'ArrowRight':
          event.preventDefault();
          seekToTime(currentTime + 10);
          break;
        case 'ArrowUp':
          event.preventDefault();
          handleVolumeChange(volume + 0.1);
          break;
        case 'ArrowDown':
          event.preventDefault();
          handleVolumeChange(volume - 0.1);
          break;
        case 'KeyM':
          event.preventDefault();
          toggleMute();
          break;
        case 'KeyF':
          event.preventDefault();
          toggleFullscreen();
          break;
        case 'Comma':
          event.preventDefault();
          goToPreviousChapter();
          break;
        case 'Period':
          event.preventDefault();
          goToNextChapter();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    togglePlayPause,
    seekToTime,
    currentTime,
    handleVolumeChange,
    volume,
    toggleMute,
    toggleFullscreen,
    goToPreviousChapter,
    goToNextChapter,
  ]);

  // Fullscreen change listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  if (error) {
    return (
      <div className={`video-player-error bg-red-50 border border-red-200 rounded-lg p-8 text-center ${className}`}>
        <div className="text-red-600 mb-2">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-red-800 mb-2">Video Load Error</h3>
        <p className="text-red-600">{error}</p>
        <Button 
          variant="secondary" 
          className="mt-4"
          onClick={() => {
            setError(null);
            setIsLoading(true);
            videoRef.current?.load();
          }}
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={`video-player bg-black rounded-lg overflow-hidden ${className}`}>
      {/* Video Element */}
      <div className="relative">
        <video
          ref={videoRef}
          className="w-full h-auto"
          src={video.streamUrl || video.fileUrl}
          autoPlay={autoPlay}
          controls={false} // We'll use custom controls
          onLoadedMetadata={handleLoadedMetadata}
          onTimeUpdate={handleTimeUpdate}
          onPlay={handlePlay}
          onPause={handlePause}
          onEnded={handleEnded}
          onError={handleError}
          poster={video.thumbnailUrl}
        />

        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <LoadingSpinner size="lg" text="Loading video..." />
          </div>
        )}

        {/* Custom Controls Overlay */}
        {showControls && !isLoading && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/70 to-transparent p-4">
            {/* Progress Bar */}
            <div className="mb-4">
              <div 
                className="w-full h-2 bg-white/20 rounded-full cursor-pointer"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const percent = (e.clientX - rect.left) / rect.width;
                  seekToTime(percent * duration);
                }}
              >
                <div 
                  className="h-full bg-white rounded-full transition-all duration-150"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center space-x-3">
                {/* Play/Pause */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={togglePlayPause}
                  className="text-white hover:bg-white/20"
                >
                  {isPlaying ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="m7 4 10 8L7 20V4z" />
                    </svg>
                  )}
                </Button>

                {/* Previous Chapter */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={goToPreviousChapter}
                  disabled={!currentChapter && chapters.length === 0}
                  className="text-white hover:bg-white/20 disabled:opacity-50"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" />
                  </svg>
                </Button>

                {/* Next Chapter */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={goToNextChapter}
                  disabled={!currentChapter && chapters.length === 0}
                  className="text-white hover:bg-white/20 disabled:opacity-50"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" />
                  </svg>
                </Button>

                {/* Time Display */}
                <span className="text-sm font-mono">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                {/* Volume Controls */}
                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleMute}
                    className="text-white hover:bg-white/20"
                  >
                    {isMuted || volume === 0 ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                      </svg>
                    )}
                  </Button>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={isMuted ? 0 : volume}
                    onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                    className="w-20 h-2 bg-white/20 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                {/* Fullscreen */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleFullscreen}
                  className="text-white hover:bg-white/20"
                >
                  {isFullscreen ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5M15 9h4.5M15 9V4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5M15 15h4.5M15 15v4.5m0-4.5l5.5 5.5" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chapter Timeline */}
      {showChapterTimeline && chapters.length > 0 && (
        <div className="p-4 bg-gray-50 border-t">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-700">Chapters</h4>
            {currentChapter && (
              <span className="text-sm text-gray-600">
                Current: {currentChapter.title}
              </span>
            )}
          </div>
          <ChapterTimeline
            video={video}
            chapters={chapters}
            currentTime={currentTime}
            onTimeChange={seekToTime}
            onChapterSelect={goToChapter}
            showLabels={true}
            showTooltips={true}
          />
        </div>
      )}

      {/* Keyboard Shortcuts Help */}
      <div className="hidden">
        {/* This is for screen readers and documentation */}
        <span>Keyboard shortcuts: Space (play/pause), ← → (seek), ↑ ↓ (volume), M (mute), F (fullscreen), , . (chapters)</span>
      </div>
    </div>
  );
};

export default VideoPlayer; 