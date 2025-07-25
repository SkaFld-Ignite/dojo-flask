// Shared TypeScript types for video processing and chapter management

export interface VideoInfo {
  id: string;
  filename: string;
  originalName: string;
  size: number; // bytes
  duration?: number; // seconds
  format: string;
  mimeType: string;
  uploadedAt: Date;
  path: string;
}

export interface Chapter {
  id: string;
  videoId: string;
  timestamp: string; // "HH:MM:SS" format
  title: string;
  startTime: number; // seconds
  endTime?: number; // seconds
  confidence?: number; // AI confidence score (0-1)
  createdAt: Date;
  isAiGenerated: boolean;
}

export type ProcessingStage = 
  | 'uploading'
  | 'extracting_audio' 
  | 'generating_transcript'
  | 'analyzing_content'
  | 'generating_chapters'
  | 'finalizing'
  | 'complete'
  | 'error';

export interface ProcessingJob {
  id: string;
  videoId: string;
  status: ProcessingStage;
  progress: number; // 0-100
  estimatedTimeRemaining?: number; // seconds
  startTime: Date;
  endTime?: Date;
  errorMessage?: string;
  stageProgress: Record<ProcessingStage, number>;
  metadata: {
    asrDuration?: number;
    transcriptLength?: number;
    chaptersGenerated?: number;
    llmInferenceTime?: number;
  };
}

export interface ProcessingStatus {
  job: ProcessingJob;
  currentStage: ProcessingStage;
  stageDescription: string;
  progressPercentage: number;
  timeElapsed: number;
  estimatedTimeRemaining?: number;
}

export type ExportFormat = 'json' | 'srt' | 'vtt' | 'csv' | 'txt';

export interface ExportOptions {
  format: ExportFormat;
  includeTimestamps: boolean;
  includeConfidence: boolean;
  chapterIds?: string[]; // Optional: export only specific chapters
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  videoId: string;
  jobId: string;
  uploadUrl?: string; // For resumable uploads
}

export interface ChapterGenerationResult {
  chapters: Chapter[];
  metadata: {
    totalChapters: number;
    averageConfidence: number;
    processingTime: number;
    model: string;
  };
}

// WebSocket event types for real-time updates
export interface WebSocketEvent {
  type: 'progress_update' | 'stage_change' | 'error' | 'complete';
  jobId: string;
  data: ProcessingStatus | { error: string } | { chapters: Chapter[] };
} 