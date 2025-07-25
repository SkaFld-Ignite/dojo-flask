'use client';

import { useState, useEffect, useCallback } from 'react';
import { Video, Chapter, ChapterExportOptions } from '../../types';
import { chapterApi } from '../../lib/api';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import LoadingSpinner from '../ui/LoadingSpinner';

interface ChapterManagerProps {
  video: Video;
  chapters: Chapter[];
  onChaptersChange?: (chapters: Chapter[]) => void;
  onChapterSelect?: (chapter: Chapter) => void;
  className?: string;
}

interface ChapterFormData {
  title: string;
  startTime: number;
  endTime?: number;
  description?: string;
  keywords?: string[];
}

interface ChapterFormErrors {
  title?: string;
  startTime?: string;
  endTime?: string;
  description?: string;
  keywords?: string;
}

const ChapterManager: React.FC<ChapterManagerProps> = ({
  video,
  chapters: initialChapters,
  onChaptersChange,
  onChapterSelect,
  className = '',
}) => {
  const [chapters, setChapters] = useState<Chapter[]>(initialChapters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingChapter, setEditingChapter] = useState<Chapter | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [draggedChapter, setDraggedChapter] = useState<Chapter | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // Format time for display (HH:MM:SS or MM:SS)
  const formatTime = useCallback((seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Parse time input (supports HH:MM:SS, MM:SS, or seconds)
  const parseTimeInput = useCallback((input: string): number => {
    const parts = input.split(':').map(p => parseInt(p, 10));
    if (parts.length === 1) {
      return parts[0] || 0;
    } else if (parts.length === 2) {
      return (parts[0] * 60) + (parts[1] || 0);
    } else if (parts.length === 3) {
      return (parts[0] * 3600) + (parts[1] * 60) + (parts[2] || 0);
    }
    return 0;
  }, []);

  // Update local state and notify parent
  const updateChapters = useCallback((newChapters: Chapter[]) => {
    setChapters(newChapters);
    onChaptersChange?.(newChapters);
  }, [onChaptersChange]);

  // Refresh chapters from API
  const refreshChapters = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await chapterApi.getByVideo(video.id);
      if (response.success && response.data) {
        updateChapters(response.data.chapters);
      } else {
        setError(response.error || 'Failed to load chapters');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [video.id, updateChapters]);

  // Create new chapter
  const handleCreateChapter = useCallback(async (formData: ChapterFormData) => {
    setLoading(true);
    setError(null);

    try {
      const newChapter: Partial<Chapter> = {
        videoId: video.id,
        title: formData.title,
        startTime: formData.startTime,
        endTime: formData.endTime,
        description: formData.description,
        keywords: formData.keywords,
        isAiGenerated: false,
        order: chapters.length,
      };

      const response = await chapterApi.create(newChapter);
      if (response.success && response.data) {
        const updatedChapters = [...chapters, response.data.chapter];
        updateChapters(updatedChapters);
        setIsCreateModalOpen(false);
      } else {
        setError(response.error || 'Failed to create chapter');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [video.id, chapters, updateChapters]);

  // Update existing chapter
  const handleUpdateChapter = useCallback(async (formData: ChapterFormData) => {
    if (!editingChapter) return;

    setLoading(true);
    setError(null);

    try {
      const updatedChapter: Partial<Chapter> = {
        title: formData.title,
        startTime: formData.startTime,
        endTime: formData.endTime,
        description: formData.description,
        keywords: formData.keywords,
      };

      const response = await chapterApi.update(editingChapter.id, updatedChapter);
      if (response.success && response.data) {
        const updatedChapters = chapters.map(ch => 
          ch.id === editingChapter.id ? response.data!.chapter : ch
        );
        updateChapters(updatedChapters);
        setIsEditModalOpen(false);
        setEditingChapter(null);
      } else {
        setError(response.error || 'Failed to update chapter');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [editingChapter, chapters, updateChapters]);

  // Delete chapter
  const handleDeleteChapter = useCallback(async (chapterId: string) => {
    if (!confirm('Are you sure you want to delete this chapter?')) return;

    setLoading(true);
    setError(null);

    try {
      const response = await chapterApi.delete(chapterId);
      if (response.success) {
        const updatedChapters = chapters.filter(ch => ch.id !== chapterId);
        updateChapters(updatedChapters);
      } else {
        setError(response.error || 'Failed to delete chapter');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [chapters, updateChapters]);

  // Handle chapter reordering
  const handleReorderChapters = useCallback(async (newOrder: Chapter[]) => {
    setLoading(true);
    setError(null);

    try {
      const chapterIds = newOrder.map(ch => ch.id);
      const response = await chapterApi.reorder(video.id, chapterIds);
      if (response.success && response.data) {
        updateChapters(response.data.chapters);
      } else {
        setError(response.error || 'Failed to reorder chapters');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [video.id, updateChapters]);

  // Drag and drop handlers
  const handleDragStart = useCallback((e: React.DragEvent, chapter: Chapter) => {
    setDraggedChapter(chapter);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    setDragOverIndex(index);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedChapter(null);
    setDragOverIndex(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    
    if (!draggedChapter) return;

    const sourceIndex = chapters.findIndex(ch => ch.id === draggedChapter.id);
    if (sourceIndex === targetIndex) return;

    const newChapters = [...chapters];
    newChapters.splice(sourceIndex, 1);
    newChapters.splice(targetIndex, 0, draggedChapter);

    updateChapters(newChapters);
    handleReorderChapters(newChapters);
  }, [draggedChapter, chapters, updateChapters, handleReorderChapters]);

  // Export chapters
  const handleExport = useCallback(async (options: ChapterExportOptions) => {
    setLoading(true);
    setError(null);

    try {
      const response = await chapterApi.export(video.id, options);
      if (response.success && response.data) {
        // Create download link
        const blob = new Blob([
          typeof response.data.exportData === 'string' 
            ? response.data.exportData 
            : JSON.stringify(response.data.exportData, null, 2)
        ], { type: 'text/plain' });
        
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = response.data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        setIsExportModalOpen(false);
      } else {
        setError(response.error || 'Failed to export chapters');
      }
    } catch (err) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  }, [video.id]);

  // Sort chapters by start time
  const sortedChapters = [...chapters].sort((a, b) => a.startTime - b.startTime);

  return (
    <div className={`chapter-manager ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Chapter Management
          </h3>
          <p className="text-sm text-gray-600">
            {chapters.length} chapters • {video.originalName}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsExportModalOpen(true)}
            disabled={chapters.length === 0}
          >
            Export
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateModalOpen(true)}
          >
            Add Chapter
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setError(null)}
            className="mt-2 text-red-600"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="mb-4 flex items-center justify-center py-4">
          <LoadingSpinner size="sm" text="Processing..." />
        </div>
      )}

      {/* Chapter List */}
      <div className="space-y-3">
        {sortedChapters.length === 0 ? (
          <div className="text-center py-8 border border-gray-200 rounded-lg">
            <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h4 className="text-lg font-medium text-gray-900 mb-2">No chapters yet</h4>
            <p className="text-gray-600 mb-4">Start by creating your first chapter or processing this video with AI.</p>
            <Button
              variant="primary"
              onClick={() => setIsCreateModalOpen(true)}
            >
              Create Chapter
            </Button>
          </div>
        ) : (
          sortedChapters.map((chapter, index) => (
            <div
              key={chapter.id}
              draggable
              onDragStart={(e) => handleDragStart(e, chapter)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              onDrop={(e) => handleDrop(e, index)}
              className={`chapter-item p-4 border rounded-lg cursor-move transition-all ${
                dragOverIndex === index 
                  ? 'border-blue-400 bg-blue-50' 
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 mb-2">
                    {/* Drag Handle */}
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
                    </svg>
                    
                    {/* Chapter Number */}
                    <span className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </span>
                    
                    {/* Title and Time */}
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {chapter.title}
                      </h4>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span>{formatTime(chapter.startTime)}</span>
                        {chapter.endTime && (
                          <>
                            <span>–</span>
                            <span>{formatTime(chapter.endTime)}</span>
                          </>
                        )}
                        {chapter.isAiGenerated && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            AI Generated
                          </span>
                        )}
                        {chapter.confidence && (
                          <span className="text-xs text-gray-400">
                            {Math.round(chapter.confidence * 100)}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Description */}
                  {chapter.description && (
                    <p className="text-sm text-gray-600 mb-2 ml-11">
                      {chapter.description}
                    </p>
                  )}
                  
                  {/* Keywords */}
                  {chapter.keywords && chapter.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 ml-11">
                      {chapter.keywords.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onChapterSelect?.(chapter)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setEditingChapter(chapter);
                      setIsEditModalOpen(true);
                    }}
                    className="text-gray-600 hover:text-gray-800"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteChapter(chapter.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Chapter Modal */}
      <ChapterFormModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateChapter}
        title="Create New Chapter"
        videoDuration={video.duration}
        existingChapters={chapters}
      />

      {/* Edit Chapter Modal */}
      <ChapterFormModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingChapter(null);
        }}
        onSubmit={handleUpdateChapter}
        title="Edit Chapter"
        videoDuration={video.duration}
        existingChapters={chapters}
        initialData={editingChapter ? {
          title: editingChapter.title,
          startTime: editingChapter.startTime,
          endTime: editingChapter.endTime,
          description: editingChapter.description || '',
          keywords: editingChapter.keywords || [],
        } : undefined}
      />

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        onExport={handleExport}
        chapters={chapters}
      />
    </div>
  );
};

// Chapter Form Modal Component
interface ChapterFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ChapterFormData) => void;
  title: string;
  videoDuration: number;
  existingChapters: Chapter[];
  initialData?: ChapterFormData;
}

const ChapterFormModal: React.FC<ChapterFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  title,
  videoDuration,
  existingChapters,
  initialData,
}) => {
  const [formData, setFormData] = useState<ChapterFormData>({
    title: '',
    startTime: 0,
    endTime: undefined,
    description: '',
    keywords: [],
  });
  const [errors, setErrors] = useState<ChapterFormErrors>({});

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setFormData(initialData || {
        title: '',
        startTime: 0,
        endTime: undefined,
        description: '',
        keywords: [],
      });
      setErrors({});
    }
  }, [isOpen, initialData]);

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const parseTimeInput = (input: string): number => {
    const parts = input.split(':').map(p => parseInt(p, 10));
    if (parts.length === 1) {
      return parts[0] || 0;
    } else if (parts.length === 2) {
      return (parts[0] * 60) + (parts[1] || 0);
    } else if (parts.length === 3) {
      return (parts[0] * 3600) + (parts[1] * 60) + (parts[2] || 0);
    }
    return 0;
  };

  const validateForm = (): boolean => {
    const newErrors: ChapterFormErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (formData.startTime < 0 || formData.startTime >= videoDuration) {
      newErrors.startTime = `Start time must be between 0 and ${formatTime(videoDuration)}`;
    }

    if (formData.endTime !== undefined) {
      if (formData.endTime <= formData.startTime) {
        newErrors.endTime = 'End time must be after start time';
      }
      if (formData.endTime > videoDuration) {
        newErrors.endTime = `End time cannot exceed video duration (${formatTime(videoDuration)})`;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleKeywordsChange = (value: string) => {
    const keywords = value.split(',').map(k => k.trim()).filter(k => k.length > 0);
    setFormData(prev => ({ ...prev, keywords }));
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chapter Title *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            className={`input-field ${errors.title ? 'border-red-300' : ''}`}
            placeholder="Enter chapter title"
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title}</p>
          )}
        </div>

        {/* Start Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Time * (MM:SS or HH:MM:SS)
          </label>
          <input
            type="text"
            value={formatTime(formData.startTime)}
            onChange={(e) => setFormData(prev => ({ ...prev, startTime: parseTimeInput(e.target.value) }))}
            className={`input-field ${errors.startTime ? 'border-red-300' : ''}`}
            placeholder="0:00"
          />
          {errors.startTime && (
            <p className="mt-1 text-sm text-red-600">{errors.startTime}</p>
          )}
        </div>

        {/* End Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Time (MM:SS or HH:MM:SS, optional)
          </label>
          <input
            type="text"
            value={formData.endTime !== undefined ? formatTime(formData.endTime) : ''}
            onChange={(e) => {
              const value = e.target.value.trim();
              setFormData(prev => ({ 
                ...prev, 
                endTime: value ? parseTimeInput(value) : undefined 
              }));
            }}
            className={`input-field ${errors.endTime ? 'border-red-300' : ''}`}
            placeholder="Leave empty for auto"
          />
          {errors.endTime && (
            <p className="mt-1 text-sm text-red-600">{errors.endTime}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            className="input-field"
            rows={3}
            placeholder="Optional chapter description"
          />
        </div>

        {/* Keywords */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Keywords (comma-separated)
          </label>
          <input
            type="text"
            value={(formData.keywords || []).join(', ')}
            onChange={(e) => handleKeywordsChange(e.target.value)}
            className="input-field"
            placeholder="keyword1, keyword2, keyword3"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
          >
            {initialData ? 'Update Chapter' : 'Create Chapter'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

// Export Modal Component
interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (options: ChapterExportOptions) => void;
  chapters: Chapter[];
}

const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  onExport,
  chapters,
}) => {
  const [format, setFormat] = useState<ChapterExportOptions['format']>('json');
  const [includeTimestamps, setIncludeTimestamps] = useState(true);
  const [includeConfidence, setIncludeConfidence] = useState(false);
  const [selectedChapters, setSelectedChapters] = useState<string[]>([]);

  const handleExport = () => {
    const options: ChapterExportOptions = {
      format,
      includeTimestamps,
      includeConfidence,
      chapterIds: selectedChapters.length > 0 ? selectedChapters : undefined,
    };
    onExport(options);
  };

  const toggleChapterSelection = (chapterId: string) => {
    setSelectedChapters(prev => 
      prev.includes(chapterId)
        ? prev.filter(id => id !== chapterId)
        : [...prev, chapterId]
    );
  };

  const selectAllChapters = () => {
    setSelectedChapters(chapters.map(ch => ch.id));
  };

  const deselectAllChapters = () => {
    setSelectedChapters([]);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Export Chapters">
      <div className="space-y-6">
        {/* Format Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Export Format
          </label>
          <div className="grid grid-cols-2 gap-3">
            {(['json', 'srt', 'vtt', 'csv', 'txt'] as const).map((formatOption) => (
              <label
                key={formatOption}
                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                  format === formatOption
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="format"
                  value={formatOption}
                  checked={format === formatOption}
                  onChange={(e) => setFormat(e.target.value as any)}
                  className="sr-only"
                />
                <span className="text-sm font-medium text-gray-900 uppercase">
                  {formatOption}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Export Options
          </label>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={includeTimestamps}
                onChange={(e) => setIncludeTimestamps(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Include timestamps</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={includeConfidence}
                onChange={(e) => setIncludeConfidence(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Include AI confidence scores</span>
            </label>
          </div>
        </div>

        {/* Chapter Selection */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-gray-700">
              Select Chapters ({selectedChapters.length} of {chapters.length})
            </label>
            <div className="flex space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAllChapters}
                className="text-blue-600"
              >
                All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={deselectAllChapters}
                className="text-gray-600"
              >
                None
              </Button>
            </div>
          </div>
          <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md">
            {chapters.map((chapter) => (
              <label
                key={chapter.id}
                className="flex items-center p-2 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedChapters.includes(chapter.id)}
                  onChange={() => toggleChapterSelection(chapter.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-900 truncate">
                  {chapter.title}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4">
          <Button
            variant="secondary"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleExport}
            disabled={chapters.length === 0}
          >
            Export Chapters
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default ChapterManager; 