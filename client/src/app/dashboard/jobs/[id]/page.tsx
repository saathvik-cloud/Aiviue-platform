'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';
import { ROUTES, WORK_TYPES } from '@/constants';
import { useJob, usePublishJob, useCloseJob } from '@/lib/hooks';
import { formatDate, formatDateTime, formatSalaryRange, capitalize } from '@/lib/utils';
import { 
  ArrowLeft,
  Edit,
  Send,
  XCircle,
  MapPin,
  Building,
  DollarSign,
  Users,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';

/**
 * Job Details Page - Glassmorphism design
 */
export default function JobDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const { data: job, isLoading, refetch } = useJob(jobId);
  const publishMutation = usePublishJob();
  const closeMutation = useCloseJob();
  
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [closeReason, setCloseReason] = useState('');

  const handlePublish = async () => {
    if (!job) return;
    
    try {
      await publishMutation.mutateAsync({
        id: job.id,
        data: { version: job.version },
      });
      toast.success('Job published successfully! Event sent to Screening Agent.');
      setShowPublishModal(false);
      refetch();
    } catch {
      toast.error('Failed to publish job');
    }
  };

  const handleClose = async () => {
    if (!job) return;
    
    try {
      await closeMutation.mutateAsync({
        id: job.id,
        data: { version: job.version, reason: closeReason || undefined },
      });
      toast.success('Job closed successfully');
      setShowCloseModal(false);
      setCloseReason('');
      refetch();
    } catch {
      toast.error('Failed to close job');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-16">
        <div 
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
          style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%)' }}
        >
          <AlertCircle className="w-8 h-8" style={{ color: 'var(--status-closed)' }} />
        </div>
        <p className="text-lg font-medium" style={{ color: 'var(--neutral-dark)' }}>Job not found</p>
        <Link href={ROUTES.JOBS} className="inline-flex items-center gap-2 mt-4 text-sm font-medium gradient-text">
          <ArrowLeft className="w-4 h-4" />
          Back to Jobs
        </Link>
      </div>
    );
  }

  const workTypeLabel = WORK_TYPES.find(t => t.value === job.work_type)?.label;

  return (
    <div className="space-y-6">
      {/* Back Button & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <Link href={ROUTES.JOBS} className="inline-flex items-center gap-2 text-sm font-medium" style={{ color: 'var(--neutral-gray)' }}>
          <ArrowLeft className="w-4 h-4" />
          Back to Jobs
        </Link>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <Link
            href={ROUTES.JOB_EDIT(job.id)}
            className="btn-glass flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium"
            style={{ color: 'var(--neutral-dark)' }}
          >
            <Edit className="w-4 h-4" />
            <span className="hidden sm:inline">Edit</span>
          </Link>

          {job.status === 'draft' && (
            <button
              onClick={() => setShowPublishModal(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-white text-sm font-medium transition-all shadow-lg hover:shadow-xl"
              style={{ background: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)' }}
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Publish</span>
            </button>
          )}

          {job.status === 'published' && (
            <button
              onClick={() => setShowCloseModal(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--status-closed)' }}
            >
              <XCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Close Job</span>
            </button>
          )}
        </div>
      </div>

      {/* Job Header Card */}
      <div className="glass-card rounded-2xl p-6 relative overflow-hidden">
        {/* Background decoration */}
        <div 
          className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-10 blur-3xl transform translate-x-10 -translate-y-10"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        
        <div className="relative">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <span className={`status-badge status-${job.status}`}>
                  {capitalize(job.status)}
                </span>
                {job.is_published && (
                  <span className="text-xs flex items-center gap-1" style={{ color: 'var(--neutral-gray)' }}>
                    <Clock className="w-3 h-3" />
                    Published {formatDate(job.published_at!)}
                  </span>
                )}
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
                {job.title}
              </h1>
            </div>
          </div>

          {/* Meta Info */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
            {job.location && (
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
                >
                  <MapPin className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                </div>
                <div>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Location</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{job.location}</p>
                </div>
              </div>
            )}

            {workTypeLabel && (
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)' }}
                >
                  <Building className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                </div>
                <div>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Work Type</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{workTypeLabel}</p>
                </div>
              </div>
            )}

            {(job.salary_range_min || job.salary_range_max) && (
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(34, 197, 94, 0.1)' }}
                >
                  <DollarSign className="w-5 h-5" style={{ color: 'var(--status-published)' }} />
                </div>
                <div>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Salary</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                    {formatSalaryRange(job.salary_range_min, job.salary_range_max)}
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3">
              <div 
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ background: 'rgba(20, 184, 166, 0.1)' }}
              >
                <Users className="w-5 h-5" style={{ color: 'var(--secondary-teal)' }} />
              </div>
              <div>
                <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Openings</p>
                <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{job.openings_count}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Description & Requirements */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--neutral-dark)' }}>
            Job Description
          </h2>
          <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--neutral-gray)' }}>
            {job.description || 'No description provided.'}
          </div>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--neutral-dark)' }}>
            Requirements
          </h2>
          <div className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--neutral-gray)' }}>
            {job.requirements || 'No requirements specified.'}
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="glass-card rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--neutral-dark)' }}>
          Additional Information
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Created</p>
            <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{formatDateTime(job.created_at)}</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Last Updated</p>
            <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{formatDateTime(job.updated_at)}</p>
          </div>
          {job.compensation && (
            <div>
              <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Compensation</p>
              <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{job.compensation}</p>
            </div>
          )}
          {job.close_reason && (
            <div>
              <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Close Reason</p>
              <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>{job.close_reason}</p>
            </div>
          )}
        </div>
      </div>

      {/* Publish Modal */}
      {showPublishModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="glass-card rounded-3xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="text-center">
              <div 
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(74, 222, 128, 0.1) 100%)' }}
              >
                <Send className="w-8 h-8" style={{ color: 'var(--status-published)' }} />
              </div>
              <h3 className="text-xl font-semibold" style={{ color: 'var(--neutral-dark)' }}>Publish Job?</h3>
              <p className="text-sm mt-2" style={{ color: 'var(--neutral-gray)' }}>
                This will make the job visible and send an event to the Screening Agent.
              </p>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowPublishModal(false)}
                className="btn-glass flex-1 px-4 py-3 rounded-xl text-sm font-medium"
                style={{ color: 'var(--neutral-dark)' }}
              >
                Cancel
              </button>
              <button
                onClick={handlePublish}
                disabled={publishMutation.isPending}
                className="flex-1 px-4 py-3 rounded-xl text-white text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg"
                style={{ background: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)' }}
              >
                {publishMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Publish
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Close Modal */}
      {showCloseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="glass-card rounded-3xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="text-center">
              <div 
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%)' }}
              >
                <XCircle className="w-8 h-8" style={{ color: 'var(--status-closed)' }} />
              </div>
              <h3 className="text-xl font-semibold" style={{ color: 'var(--neutral-dark)' }}>Close Job?</h3>
              <p className="text-sm mt-2" style={{ color: 'var(--neutral-gray)' }}>
                This will mark the job as closed. You can optionally provide a reason.
              </p>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Reason (optional)
              </label>
              <input
                type="text"
                value={closeReason}
                onChange={(e) => setCloseReason(e.target.value)}
                placeholder="e.g., Position filled"
                className="w-full px-4 py-3 rounded-xl border text-sm outline-none bg-white/50 focus:bg-white focus:ring-2"
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCloseModal(false)}
                className="btn-glass flex-1 px-4 py-3 rounded-xl text-sm font-medium"
                style={{ color: 'var(--neutral-dark)' }}
              >
                Cancel
              </button>
              <button
                onClick={handleClose}
                disabled={closeMutation.isPending}
                className="flex-1 px-4 py-3 rounded-xl text-white text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                style={{ backgroundColor: 'var(--status-closed)' }}
              >
                {closeMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <XCircle className="w-4 h-4" />
                    Close Job
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
