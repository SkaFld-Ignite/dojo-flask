// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: string[];
}

// Video Types
export interface Video {
  id: string;
  filename: string;
  originalName: string;
  fileSize: number;
  mimeType: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  bitrate: number;
  codec: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  uploadedAt: string;
  updatedAt: string;
  fileUrl: string;
  thumbnailUrl?: string;
  streamUrl?: string;
}

export interface VideoUploadProgress {
  loaded: number;
  total: number;
  progress: number;
}

export interface VideoListResponse {
  videos: Video[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// Chapter Types
export interface Chapter {
  id: string;
  videoId: string;
  title: string;
  startTime: number;
  endTime?: number;
  confidence?: number;
  isAiGenerated: boolean;
  description?: string;
  keywords?: string[];
  order: number;
  timestamp: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChapterExportOptions {
  format: 'json' | 'srt' | 'vtt' | 'csv' | 'txt';
  includeTimestamps?: boolean;
  includeConfidence?: boolean;
  chapterIds?: string[];
}

export interface ChapterExportResponse {
  exportData: string | Chapter[];
  format: string;
  totalChapters: number;
  filename: string;
}

// Processing Job Types
export type ProcessingStage = 
  | 'uploading'
  | 'processing'
  | 'transcribing'
  | 'generating'
  | 'complete'
  | 'error';

export interface ProcessingJob {
  id: string;
  videoId: string;
  status: ProcessingStage;
  progress: number;
  stageProgress: Record<string, number>;
  errorMessage?: string;
  errorDetails?: string;
  chaptersGenerated?: number;
  startTime: string;
  endTime?: string;
  createdAt: string;
  updatedAt: string;
  config: ProcessingConfig;
  metadata?: Record<string, any>;
}

export interface ProcessingConfig {
  minChapterLength?: number;
  maxChapters?: number;
  transcriptionLanguage?: string;
  initialPrompt?: string;
}

export interface ProcessingStats {
  totalJobs: number;
  activeJobs: number;
  completedJobs: number;
  failedJobs: number;
  successRate: number;
  recentActivity: number;
  byStatus: Record<string, number>;
}

// AI Processing Types
export interface ProcessingEstimate {
  videoId: string;
  duration: number;
  estimates: {
    transcription: number;
    chapter_generation: number;
    saving: number;
    total: number;
  };
  requirements: {
    device: string;
    memory_usage: any;
    ffmpeg_required: boolean;
    models_loaded: string[];
    estimated_memory_gb: number;
    recommended_free_storage_gb: number;
  };
}

export interface ModelStatus {
  device: string;
  models_loaded: string[];
  memory_usage: {
    device: string;
    models_loaded: string[];
    cuda_memory_allocated?: number;
    cuda_memory_reserved?: number;
    cuda_memory_free?: number;
  };
  model_cache_dir: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface JobProgressMessage {
  job: ProcessingJob;
  video?: Video;
}

export interface JobStageChangeMessage {
  job: ProcessingJob;
  video?: Video;
  newStage: ProcessingStage;
  stageDescription: string;
}

export interface JobCompleteMessage {
  job: ProcessingJob;
  video?: Video;
  chapters: Chapter[];
}

export interface JobErrorMessage {
  job: ProcessingJob;
  video?: Video;
  error: string;
  errorDetails?: string;
}

// UI State Types
export interface UploadState {
  isUploading: boolean;
  progress: number;
  currentFile?: File;
  error?: string;
}

export interface ProcessingState {
  activeJobs: ProcessingJob[];
  completedJobs: ProcessingJob[];
  isPolling: boolean;
  lastUpdated?: string;
}

export interface VideoPlayerState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  playbackRate: number;
  isFullscreen: boolean;
}

export interface ChapterTimelineState {
  selectedChapter?: Chapter;
  hoveredChapter?: Chapter;
  isEditing: boolean;
  editingChapter?: Chapter;
}

// Form Types
export interface VideoUploadForm {
  file: File;
  processingOptions?: ProcessingConfig;
}

export interface ChapterEditForm {
  title: string;
  startTime: number;
  endTime?: number;
  description?: string;
  keywords?: string[];
}

export interface ProcessingConfigForm extends ProcessingConfig {
  startProcessingImmediately?: boolean;
}

// Filter and Sort Types
export interface VideoFilters {
  status?: Video['processingStatus'];
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  minDuration?: number;
  maxDuration?: number;
}

export interface VideoSortOptions {
  field: 'uploadedAt' | 'duration' | 'filename' | 'fileSize';
  direction: 'asc' | 'desc';
}

export interface ChapterFilters {
  aiOnly?: boolean;
  manualOnly?: boolean;
  minConfidence?: number;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Navigation Types
export interface NavigationItem {
  label: string;
  href: string;
  icon?: React.ComponentType<any>;
  badge?: string | number;
  children?: NavigationItem[];
}

// Theme Types
export interface ThemeConfig {
  primaryColor: string;
  fontFamily: string;
  borderRadius: string;
  spacing: Record<string, string>;
  breakpoints: Record<string, string>;
}

// Export commonly used type unions
export type Status = 'idle' | 'loading' | 'success' | 'error';
export type Size = 'sm' | 'md' | 'lg';
export type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

// API endpoint types for type safety
export interface ApiEndpoints {
  // Video endpoints
  'GET /api/videos': { response: VideoListResponse };
  'POST /api/videos': { body: FormData; response: { video: Video } };
  'GET /api/videos/:id': { response: { video: Video } };
  'DELETE /api/videos/:id': { response: { message: string } };
  
  // Chapter endpoints
  'GET /api/chapters/video/:videoId': { response: { chapters: Chapter[]; video: Video; totalChapters: number } };
  'POST /api/chapters': { body: Partial<Chapter>; response: { chapter: Chapter } };
  'PUT /api/chapters/:id': { body: Partial<Chapter>; response: { chapter: Chapter } };
  'DELETE /api/chapters/:id': { response: { message: string } };
  'POST /api/chapters/video/:videoId/export': { body: ChapterExportOptions; response: ChapterExportResponse };
  
  // Processing endpoints
  'GET /api/processing/jobs/:id': { response: { job: ProcessingJob; video?: Video; chapters?: Chapter[] } };
  'POST /api/processing/jobs/:id/cancel': { response: { job: ProcessingJob } };
  'POST /api/processing/jobs/:id/restart': { response: { job: ProcessingJob } };
  'GET /api/processing/stats': { response: ProcessingStats };
  
  // AI endpoints
  'POST /api/ai/process': { body: { videoId: string } & ProcessingConfig; response: { job_id: string; task_id: string; status: string; video_id: string; estimated_time: any } };
  'GET /api/ai/status/:jobId': { response: { job: ProcessingJob; video?: Video; task_status?: any } };
  'POST /api/ai/estimate': { body: { videoId: string }; response: ProcessingEstimate };
  'GET /api/ai/models/status': { response: ModelStatus };
  'POST /api/ai/models/load': { body: { loadAsr?: boolean; loadLlm?: boolean }; response: { loaded_models: string[]; memory_usage: any } };
} 