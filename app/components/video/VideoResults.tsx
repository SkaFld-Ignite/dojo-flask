'use client';

import { useState, useEffect, useCallback } from 'react';
import { Video, Chapter } from '../../types';
import { videoApi, chapterApi } from '../../lib/api';
import { VideoPlayer } from './';
import { ChapterManager } from '../chapters';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';

interface VideoResultsProps {
  video: Video;
  initialChapters?: Chapter[];
  onClose?: () => void;
  onVideoSelect?: (video: Video) => void;
  className?: string;
}

const VideoResults: React.FC<VideoResultsProps> = ({
  video,
  initialChapters = [],
  onClose,
  onVideoSelect,
  className = '',
}) => {
  const [chapters, setChapters] = useState<Chapter[]>(initialChapters);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentChapter, setCurrentChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'player' | 'chapters'>('player');

  // Load chapters if not provided
  useEffect(() => {
    if (initialChapters.length === 0) {
      loadChapters();
    }
  }, [video.id, initialChapters.length]);

  const loadChapters = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await chapterApi.getByVideo(video.id);
      if (response.success && response.data) {
        setChapters(response.data.chapters);
      } else {
        setError(response.error || 'Failed to load chapters');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [video.id]);

  // Handle chapter changes from ChapterManager
  const handleChaptersChange = useCallback((newChapters: Chapter[]) => {
    setChapters(newChapters);
  }, []);

  // Handle chapter selection for video seeking
  const handleChapterSelect = useCallback((chapter: Chapter) => {
    setCurrentTime(chapter.startTime);
    setCurrentChapter(chapter);
    setActiveTab('player'); // Switch to player tab when chapter is selected
  }, []);

  // Handle video time updates
  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
  }, []);

  // Handle current chapter changes from video player
  const handleCurrentChapterChange = useCallback((chapter: Chapter | null) => {
    setCurrentChapter(chapter);
  }, []);

  return (
    <div className={`video-results ${className}`}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-gray-900 truncate">
              {video.originalName}
            </h2>
            <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
              <span>Duration: {Math.floor(video.duration / 60)}:{(video.duration % 60).toString().padStart(2, '0')}</span>
              <span>•</span>
              <span>{chapters.length} chapters</span>
              <span>•</span>
              <span>{Math.round(video.fileSize / 1024 / 1024)}MB</span>
              {video.processingStatus === 'completed' && (
                <>
                  <span>•</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Processing Complete
                  </span>
                </>
              )}
            </div>
          </div>
          
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="ml-4"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </Button>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="mt-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('player')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'player'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Video Player
              {currentChapter && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {currentChapter.title}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('chapters')}
              className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'chapters'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Chapter Management
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                {chapters.length}
              </span>
            </button>
          </nav>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-red-600">{error}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError(null)}
              className="ml-auto text-red-600"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" text="Loading chapters..." />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'player' && (
          <div className="h-full">
            <VideoPlayer
              video={video}
              chapters={chapters}
              onTimeUpdate={handleTimeUpdate}
              onChapterChange={handleCurrentChapterChange}
              showChapterTimeline={true}
              className="h-full"
            />
          </div>
        )}

        {activeTab === 'chapters' && (
          <div className="h-full overflow-y-auto">
            <div className="p-6">
              <ChapterManager
                video={video}
                chapters={chapters}
                onChaptersChange={handleChaptersChange}
                onChapterSelect={handleChapterSelect}
              />
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>Quick Actions:</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setActiveTab(activeTab === 'player' ? 'chapters' : 'player')}
              className="text-blue-600 hover:text-blue-800"
            >
              Switch to {activeTab === 'player' ? 'Chapters' : 'Player'}
            </Button>
            {chapters.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setActiveTab('chapters');
                  // Scroll to export section would go here
                }}
                className="text-green-600 hover:text-green-800"
              >
                Export Chapters
              </Button>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={loadChapters}
              disabled={loading}
            >
              Refresh
            </Button>
            {onVideoSelect && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onVideoSelect(video)}
              >
                Select Video
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoResults; 