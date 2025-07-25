'use client';

import { ProcessingStage } from '../../types';

interface StatusBadgeProps {
  status: ProcessingStage | string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm',
  };

  const getStatusConfig = (status: string) => {
    switch (status.toLowerCase()) {
      case 'uploading':
        return {
          label: 'Uploading',
          className: 'status-badge bg-blue-100 text-blue-800',
          icon: '⬆️',
        };
      case 'processing':
      case 'transcribing':
      case 'generating':
        return {
          label: 'Processing',
          className: 'status-badge status-processing',
          icon: '⚙️',
        };
      case 'complete':
      case 'completed':
        return {
          label: 'Complete',
          className: 'status-badge status-complete',
          icon: '✅',
        };
      case 'error':
      case 'failed':
        return {
          label: 'Failed',
          className: 'status-badge status-error',
          icon: '❌',
        };
      case 'pending':
        return {
          label: 'Pending',
          className: 'status-badge status-pending',
          icon: '⏳',
        };
      case 'cancelled':
        return {
          label: 'Cancelled',
          className: 'status-badge bg-gray-100 text-gray-800',
          icon: '🚫',
        };
      default:
        return {
          label: status,
          className: 'status-badge status-pending',
          icon: '📋',
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span 
      className={`${config.className} ${sizeClasses[size]} ${className}`}
      role="status"
      aria-label={`Status: ${config.label}`}
    >
      <span className="mr-1" aria-hidden="true">
        {config.icon}
      </span>
      {config.label}
    </span>
  );
};

export default StatusBadge; 