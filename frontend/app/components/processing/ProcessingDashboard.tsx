'use client';

import { useState, useEffect, useCallback } from 'react';
import { ProcessingJob, Video, Chapter } from '../../types';
import { aiApi, processingApi, wsConnection } from '../../lib/api';
import StatusBadge from '../ui/StatusBadge';
import ProgressBar from '../ui/ProgressBar';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';

interface ProcessingDashboardProps {
  onJobComplete?: (job: ProcessingJob, video: Video, chapters: Chapter[]) => void;
  className?: string;
}

const ProcessingDashboard: React.FC<ProcessingDashboardProps> = ({
  onJobComplete,
  className = '',
}) => {
  const [activeJobs, setActiveJobs] = useState<ProcessingJob[]>([]);
  const [recentJobs, setRecentJobs] = useState<ProcessingJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);

  // Load active jobs
  const loadActiveJobs = useCallback(async () => {
    try {
      const response = await aiApi.getActiveJobs();
      if (response.success && response.data) {
        setActiveJobs(response.data.activeJobs || []);
      }
    } catch (error) {
      console.error('Failed to load active jobs:', error);
    }
  }, []);

  // Load processing statistics
  const loadStats = useCallback(async () => {
    try {
      const response = await processingApi.getStats();
      if (response.success && response.data) {
        // Handle stats if needed
        console.log('Processing stats:', response.data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }, []);

  // WebSocket message handlers
  const handleJobProgress = useCallback((data: any) => {
    setActiveJobs(prev => prev.map(job => 
      job.id === data.job.id ? { ...job, ...data.job } : job
    ));
  }, []);

  const handleJobComplete = useCallback((data: any) => {
    const { job, video, chapters } = data;
    
    // Remove from active jobs
    setActiveJobs(prev => prev.filter(j => j.id !== job.id));
    
    // Add to recent jobs
    setRecentJobs(prev => [job, ...prev.slice(0, 9)]); // Keep last 10
    
    // Notify parent component
    onJobComplete?.(job, video, chapters || []);
  }, [onJobComplete]);

  const handleJobError = useCallback((data: any) => {
    setActiveJobs(prev => prev.map(job => 
      job.id === data.job.id ? { ...job, ...data.job } : job
    ));
  }, []);

  // Initialize dashboard
  useEffect(() => {
    const initialize = async () => {
      setIsLoading(true);
      
      try {
        // Load initial data
        await Promise.all([loadActiveJobs(), loadStats()]);
        
        // Connect to WebSocket
        if (!wsConnection.isConnected) {
          await wsConnection.connect();
        }
        
        // Subscribe to job events
        wsConnection.subscribe('job_progress', handleJobProgress);
        wsConnection.subscribe('job_complete', handleJobComplete);
        wsConnection.subscribe('job_error', handleJobError);
        
        setIsConnected(wsConnection.isConnected);
      } catch (error) {
        console.error('Failed to initialize dashboard:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initialize();

    // Cleanup on unmount
    return () => {
      wsConnection.unsubscribe('job_progress', handleJobProgress);
      wsConnection.unsubscribe('job_complete', handleJobComplete);
      wsConnection.unsubscribe('job_error', handleJobError);
    };
  }, [loadActiveJobs, loadStats, handleJobProgress, handleJobComplete, handleJobError]);

  // Job action handlers
  const handleCancelJob = async (jobId: string) => {
    try {
      const response = await aiApi.cancel(jobId);
      if (response.success) {
        setActiveJobs(prev => prev.filter(job => job.id !== jobId));
      }
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const handleRestartJob = async (jobId: string) => {
    try {
      const response = await aiApi.restart(jobId);
      if (response.success) {
        // Refresh active jobs
        await loadActiveJobs();
      }
    } catch (error) {
      console.error('Failed to restart job:', error);
    }
  };

  const getStageDescription = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'uploading':
        return 'Uploading video file...';
      case 'processing':
        return 'Initializing AI processing...';
      case 'transcribing':
        return 'Transcribing audio with speech recognition...';
      case 'generating':
        return 'Generating chapters with AI...';
      case 'complete':
        return 'Processing completed successfully!';
      case 'error':
        return 'Processing encountered an error';
      default:
        return 'Processing video...';
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className={`${className}`}>
        <LoadingSpinner size="lg" text="Loading processing dashboard..." />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Processing Dashboard
        </h2>
        <div className="flex items-center space-x-2">
          <div
            className={`h-2 w-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live updates' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Active Jobs */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">
            Active Processing Jobs
            {activeJobs.length > 0 && (
              <span className="ml-2 text-sm text-gray-500">
                ({activeJobs.length})
              </span>
            )}
          </h3>
        </div>
        <div className="card-body">
          {activeJobs.length === 0 ? (
            <div className="text-center py-8">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                No active jobs
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Upload a video to start AI processing
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {activeJobs.map((job) => (
                <div
                  key={job.id}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-medium text-gray-900">
                          Job #{job.id.slice(0, 8)}...
                        </h4>
                        <StatusBadge status={job.status} size="sm" />
                      </div>
                      <p className="text-sm text-gray-600">
                        {getStageDescription(job.status)}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      {job.status !== 'complete' && job.status !== 'error' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleCancelJob(job.id)}
                        >
                          Cancel
                        </Button>
                      )}
                      {job.status === 'error' && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleRestartJob(job.id)}
                        >
                          Restart
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <ProgressBar
                    progress={job.progress || 0}
                    showLabel
                    label={`Progress: ${Math.round(job.progress || 0)}%`}
                    color={job.status === 'error' ? 'red' : 'blue'}
                    className="mb-3"
                  />

                  {/* Job Details */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Started:</span>
                      <span className="ml-2 text-gray-900">
                        {new Date(job.startTime).toLocaleTimeString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Video ID:</span>
                      <span className="ml-2 text-gray-900 font-mono">
                        {job.videoId.slice(0, 8)}...
                      </span>
                    </div>
                  </div>

                  {/* Error Message */}
                  {job.errorMessage && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                      <p className="text-sm text-red-700">
                        <strong>Error:</strong> {job.errorMessage}
                      </p>
                    </div>
                  )}

                  {/* Stage Progress */}
                  {job.stageProgress && Object.keys(job.stageProgress).length > 0 && (
                    <div className="mt-3">
                      <h5 className="text-sm font-medium text-gray-700 mb-2">
                        Stage Progress:
                      </h5>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(job.stageProgress).map(([stage, progress]) => (
                          <div key={stage} className="flex justify-between">
                            <span className="capitalize text-gray-600">
                              {stage.replace('_', ' ')}:
                            </span>
                            <span className="text-gray-900">
                              {Math.round(progress)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Jobs */}
      {recentJobs.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Recent Completed Jobs
            </h3>
          </div>
          <div className="card-body">
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0"
                >
                  <div className="flex items-center space-x-3">
                    <StatusBadge status={job.status} size="sm" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Job #{job.id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-gray-500">
                        Completed {new Date(job.endTime || job.updatedAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    {job.chaptersGenerated && (
                      <p className="text-sm text-gray-900">
                        {job.chaptersGenerated} chapters
                      </p>
                    )}
                    <p className="text-xs text-gray-500">
                      Video: {job.videoId.slice(0, 8)}...
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProcessingDashboard; 