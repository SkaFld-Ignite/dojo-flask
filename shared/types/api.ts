// Shared API types for request/response interfaces

import { VideoInfo, Chapter, ProcessingJob, ExportFormat, ExportOptions } from './video';

// Upload API Types
export interface UploadVideoRequest {
  file: File;
  options?: {
    generateChapters?: boolean;
    model?: string;
  };
}

export interface UploadVideoResponse {
  success: boolean;
  data: {
    videoId: string;
    jobId: string;
    video: VideoInfo;
  };
  error?: string;
}

// Processing API Types
export interface GetJobStatusRequest {
  jobId: string;
}

export interface GetJobStatusResponse {
  success: boolean;
  data: {
    job: ProcessingJob;
    video: VideoInfo;
    chapters?: Chapter[];
  };
  error?: string;
}

export interface CancelJobRequest {
  jobId: string;
}

export interface CancelJobResponse {
  success: boolean;
  message: string;
  error?: string;
}

// Chapter API Types
export interface GetChaptersRequest {
  videoId: string;
}

export interface GetChaptersResponse {
  success: boolean;
  data: {
    chapters: Chapter[];
    video: VideoInfo;
  };
  error?: string;
}

export interface UpdateChapterRequest {
  chapterId: string;
  updates: Partial<Pick<Chapter, 'title' | 'startTime' | 'endTime'>>;
}

export interface UpdateChapterResponse {
  success: boolean;
  data: Chapter;
  error?: string;
}

export interface DeleteChapterRequest {
  chapterId: string;
}

export interface DeleteChapterResponse {
  success: boolean;
  message: string;
  error?: string;
}

export interface CreateChapterRequest {
  videoId: string;
  chapter: Omit<Chapter, 'id' | 'videoId' | 'createdAt' | 'isAiGenerated'>;
}

export interface CreateChapterResponse {
  success: boolean;
  data: Chapter;
  error?: string;
}

// Export API Types
export interface ExportChaptersRequest {
  videoId: string;
  options: ExportOptions;
}

export interface ExportChaptersResponse {
  success: boolean;
  data: {
    downloadUrl: string;
    filename: string;
    format: ExportFormat;
    size: number;
  };
  error?: string;
}

// Video API Types
export interface GetVideoRequest {
  videoId: string;
}

export interface GetVideoResponse {
  success: boolean;
  data: {
    video: VideoInfo;
    chapters: Chapter[];
    processingJob?: ProcessingJob;
  };
  error?: string;
}

export interface DeleteVideoRequest {
  videoId: string;
}

export interface DeleteVideoResponse {
  success: boolean;
  message: string;
  error?: string;
}

export interface ListVideosRequest {
  page?: number;
  limit?: number;
  sortBy?: 'uploadedAt' | 'filename' | 'duration';
  sortOrder?: 'asc' | 'desc';
}

export interface ListVideosResponse {
  success: boolean;
  data: {
    videos: VideoInfo[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      pages: number;
    };
  };
  error?: string;
}

// Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

export interface ValidationError extends ApiError {
  code: 'VALIDATION_ERROR';
  details: {
    field: string;
    message: string;
  }[];
}

export interface ProcessingError extends ApiError {
  code: 'PROCESSING_ERROR';
  details: {
    stage: string;
    originalError: string;
  };
}

export interface NotFoundError extends ApiError {
  code: 'NOT_FOUND';
  details: {
    resource: string;
    id: string;
  };
}

export interface RateLimitError extends ApiError {
  code: 'RATE_LIMIT';
  details: {
    limit: number;
    windowMs: number;
    retryAfter: number;
  };
} 