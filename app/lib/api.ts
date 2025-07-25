import { 
  ApiResponse, 
  Video, 
  VideoListResponse, 
  Chapter, 
  ChapterExportOptions, 
  ChapterExportResponse,
  ProcessingJob, 
  ProcessingConfig, 
  ProcessingEstimate,
  ProcessingStats,
  ModelStatus
} from '../types';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Helper function to get full API URL
const getApiUrl = (endpoint: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

// Request headers
const getHeaders = (includeContentType = true): HeadersInit => {
  const headers: HeadersInit = {
    'Accept': 'application/json',
  };
  
  if (includeContentType) {
    headers['Content-Type'] = 'application/json';
  }
  
  return headers;
};

// Generic request handler with error handling
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...getHeaders(!options.body || !(options.body instanceof FormData)),
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || data.message || `HTTP ${response.status}`);
    }

    return {
      success: true,
      data: data.data || data,
      message: data.message,
    };
  } catch (error) {
    console.error('API Request Error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
}

// Video API
export const videoApi = {
  // Upload video with progress tracking
  async upload(
    file: File, 
    processingOptions?: ProcessingConfig,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<{ video: Video }>> {
    return new Promise((resolve) => {
      const formData = new FormData();
      formData.append('video', file);
      
      if (processingOptions) {
        Object.entries(processingOptions).forEach(([key, value]) => {
          if (value !== undefined) {
            formData.append(key, String(value));
          }
        });
      }

      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve({
              success: true,
              data: data.data || data,
              message: data.message,
            });
          } catch (error) {
            resolve({
              success: false,
              error: 'Failed to parse response',
            });
          }
        } else {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve({
              success: false,
              error: data.error || data.message || `HTTP ${xhr.status}`,
            });
          } catch {
            resolve({
              success: false,
              error: `HTTP ${xhr.status}`,
            });
          }
        }
      });

      xhr.addEventListener('error', () => {
        resolve({
          success: false,
          error: 'Network error occurred',
        });
      });

      xhr.open('POST', `${API_BASE_URL}/api/videos`);
      xhr.send(formData);
    });
  },

  // Get list of videos
  async list(params?: {
    page?: number;
    limit?: number;
    status?: string;
    search?: string;
  }): Promise<ApiResponse<VideoListResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', String(params.page));
    if (params?.limit) searchParams.append('limit', String(params.limit));
    if (params?.status) searchParams.append('status', params.status);
    if (params?.search) searchParams.append('search', params.search);
    
    const query = searchParams.toString();
    return apiRequest<VideoListResponse>(`/api/videos${query ? `?${query}` : ''}`);
  },

  // Get single video
  async get(id: string): Promise<ApiResponse<{ video: Video }>> {
    return apiRequest<{ video: Video }>(`/api/videos/${id}`);
  },

  // Delete video
  async delete(id: string): Promise<ApiResponse<{ message: string }>> {
    return apiRequest<{ message: string }>(`/api/videos/${id}`, {
      method: 'DELETE',
    });
  },

  // Get video stream URL
  getStreamUrl(id: string): string {
    return `${API_BASE_URL}/api/videos/${id}/stream`;
  },

  // Get video download URL
  getDownloadUrl(id: string): string {
    return `${API_BASE_URL}/api/videos/${id}/download`;
  },
};

// Chapter API
export const chapterApi = {
  // Get chapters for video
  async getByVideo(videoId: string, params?: {
    aiOnly?: boolean;
    manualOnly?: boolean;
  }): Promise<ApiResponse<{ chapters: Chapter[]; video: Video; totalChapters: number }>> {
    const searchParams = new URLSearchParams();
    if (params?.aiOnly) searchParams.append('aiOnly', 'true');
    if (params?.manualOnly) searchParams.append('manualOnly', 'true');
    
    const query = searchParams.toString();
    return apiRequest<{ chapters: Chapter[]; video: Video; totalChapters: number }>(
      `/api/chapters/video/${videoId}${query ? `?${query}` : ''}`
    );
  },

  // Create chapter
  async create(chapter: Partial<Chapter>): Promise<ApiResponse<{ chapter: Chapter }>> {
    return apiRequest<{ chapter: Chapter }>('/api/chapters', {
      method: 'POST',
      body: JSON.stringify(chapter),
    });
  },

  // Update chapter
  async update(id: string, chapter: Partial<Chapter>): Promise<ApiResponse<{ chapter: Chapter }>> {
    return apiRequest<{ chapter: Chapter }>(`/api/chapters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(chapter),
    });
  },

  // Delete chapter
  async delete(id: string): Promise<ApiResponse<{ message: string }>> {
    return apiRequest<{ message: string }>(`/api/chapters/${id}`, {
      method: 'DELETE',
    });
  },

  // Export chapters
  async export(videoId: string, options: ChapterExportOptions): Promise<ApiResponse<ChapterExportResponse>> {
    return apiRequest<ChapterExportResponse>(`/api/chapters/video/${videoId}/export`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  },

  // Reorder chapters
  async reorder(videoId: string, chapterIds: string[]): Promise<ApiResponse<{ chapters: Chapter[] }>> {
    return apiRequest<{ chapters: Chapter[] }>(`/api/chapters/video/${videoId}/reorder`, {
      method: 'POST',
      body: JSON.stringify({ chapterIds }),
    });
  },
};

// Processing API
export const processingApi = {
  // Get job status
  async getJobStatus(jobId: string): Promise<ApiResponse<{ job: ProcessingJob; video?: Video; chapters?: Chapter[] }>> {
    return apiRequest<{ job: ProcessingJob; video?: Video; chapters?: Chapter[] }>(`/api/processing/jobs/${jobId}`);
  },

  // Cancel job
  async cancelJob(jobId: string): Promise<ApiResponse<{ job: ProcessingJob }>> {
    return apiRequest<{ job: ProcessingJob }>(`/api/processing/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  },

  // Restart job
  async restartJob(jobId: string): Promise<ApiResponse<{ job: ProcessingJob }>> {
    return apiRequest<{ job: ProcessingJob }>(`/api/processing/jobs/${jobId}/restart`, {
      method: 'POST',
    });
  },

  // Get processing statistics
  async getStats(): Promise<ApiResponse<ProcessingStats>> {
    return apiRequest<ProcessingStats>('/api/processing/stats');
  },

  // Get active jobs
  async getActiveJobs(): Promise<ApiResponse<{ activeJobs: any[]; totalActive: number }>> {
    return apiRequest<{ activeJobs: any[]; totalActive: number }>('/api/processing/jobs/active');
  },
};

// AI Processing API
export const aiApi = {
  // Start AI processing
  async startProcessing(
    videoId: string, 
    options?: ProcessingConfig
  ): Promise<ApiResponse<{ job_id: string; task_id: string; status: string; video_id: string; estimated_time: any }>> {
    return apiRequest<{ job_id: string; task_id: string; status: string; video_id: string; estimated_time: any }>('/api/ai/process', {
      method: 'POST',
      body: JSON.stringify({
        videoId,
        ...options,
      }),
    });
  },

  // Get processing status
  async getStatus(jobId: string): Promise<ApiResponse<{ job: ProcessingJob; video?: Video; task_status?: any }>> {
    return apiRequest<{ job: ProcessingJob; video?: Video; task_status?: any }>(`/api/ai/status/${jobId}`);
  },

  // Cancel processing
  async cancel(jobId: string): Promise<ApiResponse<{ job_id: string; status: string; message: string }>> {
    return apiRequest<{ job_id: string; status: string; message: string }>(`/api/ai/cancel/${jobId}`, {
      method: 'POST',
    });
  },

  // Restart processing
  async restart(jobId: string): Promise<ApiResponse<{ job_id: string; task_id: string; status: string; message: string }>> {
    return apiRequest<{ job_id: string; task_id: string; status: string; message: string }>(`/api/ai/restart/${jobId}`, {
      method: 'POST',
    });
  },

  // Get active jobs
  async getActiveJobs(): Promise<ApiResponse<{ activeJobs: any[]; totalActive: number }>> {
    return apiRequest<{ activeJobs: any[]; totalActive: number }>('/api/ai/jobs/active');
  },

  // Estimate processing time
  async estimate(videoId: string): Promise<ApiResponse<ProcessingEstimate>> {
    return apiRequest<ProcessingEstimate>('/api/ai/estimate', {
      method: 'POST',
      body: JSON.stringify({ videoId }),
    });
  },

  // Model management
  async getModelStatus(): Promise<ApiResponse<ModelStatus>> {
    return apiRequest<ModelStatus>('/api/ai/models/status');
  },

  async loadModels(options?: { loadAsr?: boolean; loadLlm?: boolean }): Promise<ApiResponse<{ loaded_models: string[]; memory_usage: any }>> {
    return apiRequest<{ loaded_models: string[]; memory_usage: any }>('/api/ai/models/load', {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  },

  async unloadModels(options?: { unloadAsr?: boolean; unloadLlm?: boolean }): Promise<ApiResponse<{ unloaded_models: string[]; memory_usage: any }>> {
    return apiRequest<{ unloaded_models: string[]; memory_usage: any }>('/api/ai/models/unload', {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  },

  // Configuration management
  async getConfig(): Promise<ApiResponse<{ config: ProcessingConfig; device: string }>> {
    return apiRequest<{ config: ProcessingConfig; device: string }>('/api/ai/config');
  },

  async updateConfig(config: ProcessingConfig): Promise<ApiResponse<{ config: ProcessingConfig }>> {
    return apiRequest<{ config: ProcessingConfig }>('/api/ai/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  // Cleanup resources
  async cleanup(options?: { cleanupModels?: boolean; cleanupJobs?: boolean; maxAgeDays?: number }): Promise<ApiResponse<any>> {
    return apiRequest<any>('/api/ai/cleanup', {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });
  },
};

// Health check API
export const healthApi = {
  async check(): Promise<ApiResponse<{ status: string; timestamp: string; version: string }>> {
    return apiRequest<{ status: string; timestamp: string; version: string }>('/api/health');
  },

  async detailed(): Promise<ApiResponse<any>> {
    return apiRequest<any>('/api/health/detailed');
  },
};

// WebSocket connection helper
export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  constructor(private url: string = WS_BASE_URL) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: any) {
    const listeners = this.listeners.get(message.type);
    if (listeners) {
      listeners.forEach(listener => listener(message.data));
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  subscribe(eventType: string, callback: (data: any) => void) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
  }

  unsubscribe(eventType: string, callback: (data: any) => void) {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      listeners.delete(callback);
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const wsConnection = new WebSocketConnection();

// Utility functions
export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${Math.round(bytes / Math.pow(1024, i) * 100) / 100} ${sizes[i]}`;
};

export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

export const formatTimestamp = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}; 