'use client';

import { useState, useCallback, useRef } from 'react';
import { videoApi } from '../../lib/api';
import { ProcessingConfig, Video } from '../../types';
import Button from '../ui/Button';
import ProgressBar from '../ui/ProgressBar';
import Modal from '../ui/Modal';

interface VideoUploadProps {
  onUploadComplete?: (video: Video) => void;
  onUploadStart?: () => void;
  className?: string;
}

interface UploadState {
  isDragging: boolean;
  isUploading: boolean;
  progress: number;
  error: string | null;
  currentFile: File | null;
}

const VideoUpload: React.FC<VideoUploadProps> = ({
  onUploadComplete,
  onUploadStart,
  className = '',
}) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    isDragging: false,
    isUploading: false,
    progress: 0,
    error: null,
    currentFile: null,
  });

  const [showConfigModal, setShowConfigModal] = useState(false);
  const [processingConfig, setProcessingConfig] = useState<ProcessingConfig>({
    minChapterLength: 30,
    maxChapters: 15,
    transcriptionLanguage: '',
    initialPrompt: '',
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Supported video formats
  const supportedFormats = [
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'video/avi',
    'video/x-msvideo',
    'video/x-ms-wmv',
  ];

  const maxFileSize = 500 * 1024 * 1024; // 500MB

  const validateFile = (file: File): string | null => {
    if (!supportedFormats.includes(file.type)) {
      return 'Unsupported file format. Please upload MP4, WebM, MOV, AVI, or WMV files.';
    }

    if (file.size > maxFileSize) {
      return 'File too large. Maximum size is 500MB.';
    }

    return null;
  };

  const resetUploadState = () => {
    setUploadState({
      isDragging: false,
      isUploading: false,
      progress: 0,
      error: null,
      currentFile: null,
    });
  };

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    const error = validateFile(file);

    if (error) {
      setUploadState(prev => ({ ...prev, error, currentFile: null }));
      return;
    }

    setUploadState(prev => ({
      ...prev,
      currentFile: file,
      error: null,
    }));

    // Show configuration modal
    setShowConfigModal(true);
  }, []);

  const startUpload = async () => {
    if (!uploadState.currentFile) return;

    setUploadState(prev => ({ ...prev, isUploading: true, progress: 0 }));
    setShowConfigModal(false);
    onUploadStart?.();

    try {
      const response = await videoApi.upload(
        uploadState.currentFile,
        processingConfig,
        (progress) => {
          setUploadState(prev => ({ ...prev, progress }));
        }
      );

      if (response.success && response.data) {
        onUploadComplete?.(response.data.video);
        resetUploadState();
      } else {
        setUploadState(prev => ({
          ...prev,
          error: response.error || 'Upload failed',
          isUploading: false,
        }));
      }
    } catch (error) {
      setUploadState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Upload failed',
        isUploading: false,
      }));
    }
  };

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setUploadState(prev => ({ ...prev, isDragging: true }));
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Only hide drag state if leaving the drop zone entirely
    if (dropZoneRef.current && !dropZoneRef.current.contains(e.relatedTarget as Node)) {
      setUploadState(prev => ({ ...prev, isDragging: false }));
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    setUploadState(prev => ({ ...prev, isDragging: false }));
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
  };

  return (
    <>
      <div className={`w-full ${className}`}>
        {/* Upload Area */}
        <div
          ref={dropZoneRef}
          className={`
            drop-zone
            ${uploadState.isDragging ? 'drop-zone-active' : ''}
            ${uploadState.isUploading ? 'opacity-75 pointer-events-none' : ''}
          `}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={openFileDialog}
          role="button"
          tabIndex={0}
          aria-label="Upload video file"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              openFileDialog();
            }
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={supportedFormats.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
            disabled={uploadState.isUploading}
          />

          {uploadState.isUploading ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center">
                <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Uploading {uploadState.currentFile?.name}
                </h3>
                <ProgressBar
                  progress={uploadState.progress}
                  showLabel
                  label="Upload Progress"
                  className="w-full"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-center">
                <svg
                  className="h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {uploadState.isDragging ? 'Drop your video here' : 'Upload Video for AI Chaptering'}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Drag and drop your video file here, or click to browse
                </p>
                <div className="text-xs text-gray-500">
                  <p>Supported formats: MP4, WebM, MOV, AVI, WMV</p>
                  <p>Maximum file size: 500MB</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {uploadState.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <svg
                className="h-5 w-5 text-red-400 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-sm text-red-700">{uploadState.error}</span>
            </div>
            <button
              onClick={resetUploadState}
              className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
            >
              Try again
            </button>
          </div>
        )}
      </div>

      {/* Processing Configuration Modal */}
      <Modal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        title="AI Processing Configuration"
        size="md"
      >
        <div className="space-y-6">
          {uploadState.currentFile && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Selected File</h4>
              <div className="text-sm text-gray-600">
                <p><strong>Name:</strong> {uploadState.currentFile.name}</p>
                <p><strong>Size:</strong> {formatFileSize(uploadState.currentFile.size)}</p>
                <p><strong>Type:</strong> {uploadState.currentFile.type}</p>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="form-label">
                Minimum Chapter Length (seconds)
              </label>
              <input
                type="number"
                min="15"
                max="300"
                value={processingConfig.minChapterLength || 30}
                onChange={(e) =>
                  setProcessingConfig(prev => ({
                    ...prev,
                    minChapterLength: parseInt(e.target.value) || 30,
                  }))
                }
                className="form-input"
              />
              <p className="text-xs text-gray-500 mt-1">
                Minimum length for generated chapters (15-300 seconds)
              </p>
            </div>

            <div>
              <label className="form-label">
                Maximum Number of Chapters
              </label>
              <input
                type="number"
                min="3"
                max="20"
                value={processingConfig.maxChapters || 15}
                onChange={(e) =>
                  setProcessingConfig(prev => ({
                    ...prev,
                    maxChapters: parseInt(e.target.value) || 15,
                  }))
                }
                className="form-input"
              />
              <p className="text-xs text-gray-500 mt-1">
                Maximum number of chapters to generate (3-20)
              </p>
            </div>

            <div>
              <label className="form-label">
                Transcription Language (optional)
              </label>
              <select
                value={processingConfig.transcriptionLanguage || ''}
                onChange={(e) =>
                  setProcessingConfig(prev => ({
                    ...prev,
                    transcriptionLanguage: e.target.value,
                  }))
                }
                className="form-input"
              >
                <option value="">Auto-detect</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="ru">Russian</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="zh">Chinese</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Leave empty for automatic language detection
              </p>
            </div>

            <div>
              <label className="form-label">
                Initial Prompt (optional)
              </label>
              <textarea
                rows={3}
                value={processingConfig.initialPrompt || ''}
                onChange={(e) =>
                  setProcessingConfig(prev => ({
                    ...prev,
                    initialPrompt: e.target.value,
                  }))
                }
                className="form-input"
                placeholder="Provide context or keywords to guide the AI..."
              />
              <p className="text-xs text-gray-500 mt-1">
                Optional prompt to guide the AI processing
              </p>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button
              variant="secondary"
              onClick={() => setShowConfigModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={startUpload}
              disabled={!uploadState.currentFile}
            >
              Start Upload & Processing
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};

export default VideoUpload; 