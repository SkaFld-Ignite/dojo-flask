'use client';

import { useState } from 'react';
import { Video, ProcessingJob, Chapter } from './types';
import VideoUpload from './components/upload/VideoUpload';
import ProcessingDashboard from './components/processing/ProcessingDashboard';
import { VideoResults } from './components/video';

export default function Home() {
  const [recentVideo, setRecentVideo] = useState<Video | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [completedVideo, setCompletedVideo] = useState<{ video: Video; chapters: Chapter[] } | null>(null);
  const [currentView, setCurrentView] = useState<'upload' | 'results'>('upload');

  const handleUploadComplete = (video: Video) => {
    setRecentVideo(video);
    setShowSuccess(true);
    
    // Hide success message after 5 seconds
    setTimeout(() => setShowSuccess(false), 5000);
  };

  const handleUploadStart = () => {
    setShowSuccess(false);
  };

  const handleJobComplete = (job: ProcessingJob, video: Video, chapters: Chapter[]) => {
    console.log('Job completed:', { job, video, chapters });
    
    // Store completed video and chapters for results view
    setCompletedVideo({ video, chapters });
    
    // Show notification and option to view results
    setShowSuccess(false);
    // Could add a toast notification here
  };

  const handleViewResults = () => {
    if (completedVideo) {
      setCurrentView('results');
    }
  };

  const handleBackToUpload = () => {
    setCurrentView('upload');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container-responsive py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                AI Video Chaptering
              </h1>
              <p className="mt-1 text-lg text-gray-600">
                Automatically generate chapters for your videos using AI
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Navigation */}
              {currentView === 'results' && (
                <button
                  onClick={handleBackToUpload}
                  className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to Upload
                </button>
              )}
              
              <div className="text-right">
                <p className="text-sm text-gray-500">Powered by</p>
                <p className="text-lg font-semibold text-blue-600">
                  Chapter-Llama
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container-responsive py-8">
        {/* Completion Notification */}
        {completedVideo && currentView === 'upload' && (
          <div className="mb-8 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="h-6 w-6 text-green-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 className="text-lg font-semibold text-green-800">
                    Processing Complete!
                  </h3>
                  <p className="text-sm text-green-700">
                    {completedVideo.video.originalName} has been processed and {completedVideo.chapters.length} chapters have been generated.
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleViewResults}
                  className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors"
                >
                  View Results
                </button>
                <button
                  onClick={() => setCompletedVideo(null)}
                  className="text-green-600 hover:text-green-800 text-sm"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        )}

        {currentView === 'upload' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2">
            <div className="card">
              <div className="card-header">
                <h2 className="text-xl font-semibold text-gray-900">
                  Upload Video
                </h2>
                <p className="text-sm text-gray-600">
                  Upload your video to generate AI-powered chapters
                </p>
              </div>
              <div className="card-body">
                <VideoUpload
                  onUploadComplete={handleUploadComplete}
                  onUploadStart={handleUploadStart}
                />

                {/* Success Message */}
                {showSuccess && recentVideo && (
                  <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
                    <div className="flex items-center">
                      <svg
                        className="h-5 w-5 text-green-400 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      <div>
                        <h3 className="text-sm font-medium text-green-800">
                          Upload Successful!
                        </h3>
                        <p className="text-sm text-green-700">
                          {recentVideo.originalName} has been uploaded and AI processing has started.
                          You can monitor the progress in the dashboard.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Features Section */}
            <div className="mt-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                AI Processing Features
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="card">
                  <div className="card-body">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-6 w-6 text-blue-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          Speech Recognition
                        </h3>
                        <p className="text-sm text-gray-600">
                          Powered by faster-whisper with word-level timestamps and voice activity detection
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="card-body">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-6 w-6 text-green-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          AI Chapter Generation
                        </h3>
                        <p className="text-sm text-gray-600">
                          Llama-3.1-8B-Instruct analyzes content and generates meaningful chapters with confidence scores
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="card-body">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-6 w-6 text-purple-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 10V3L4 14h7v7l9-11h-7z"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          Real-time Processing
                        </h3>
                        <p className="text-sm text-gray-600">
                          Background job processing with live progress updates via WebSocket
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="card-body">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <svg
                          className="h-6 w-6 text-orange-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-gray-900">
                          Multiple Export Formats
                        </h3>
                        <p className="text-sm text-gray-600">
                          Export chapters in JSON, SRT, VTT, CSV, or TXT formats
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Processing Dashboard */}
          <div>
            <ProcessingDashboard
              onJobComplete={handleJobComplete}
            />
          </div>
        </div>
        )}

        {currentView === 'results' && completedVideo && (
          <div className="max-w-7xl mx-auto">
            <VideoResults
              video={completedVideo.video}
              initialChapters={completedVideo.chapters}
              onClose={handleBackToUpload}
              className="bg-white rounded-lg shadow-sm border border-gray-200 min-h-[600px]"
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="container-responsive py-6">
          <div className="text-center text-sm text-gray-600">
            <p>
              Built with{' '}
              <span className="text-red-500">❤️</span>{' '}
              using Next.js, Flask, and Chapter-Llama AI
            </p>
            <p className="mt-1">
              Powered by faster-whisper and Llama-3.1-8B-Instruct
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
