'use client';

/**
 * Candidate Job Detail Page - Read-only view of a published job.
 */

import { ROUTES } from '@/constants';
import { useJob } from '@/lib/hooks';
import { formatDate } from '@/lib/utils';
import {
  ArrowLeft,
  Briefcase,
  MapPin,
  Building2,
  DollarSign,
  Clock,
  FileText,
} from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function CandidateJobDetailPage() {
  const params = useParams();
  const jobId = typeof params.id === 'string' ? params.id : undefined;
  const { data: job, isLoading, error } = useJob(jobId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 rounded-lg animate-pulse" style={{ background: 'var(--neutral-light)' }} />
        <div className="glass-card rounded-2xl p-6 animate-pulse space-y-4">
          <div className="h-6 rounded w-3/4" style={{ background: 'var(--neutral-light)' }} />
          <div className="h-4 rounded w-1/2" style={{ background: 'var(--neutral-light)' }} />
          <div className="h-20 rounded w-full" style={{ background: 'var(--neutral-light)' }} />
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="glass-card rounded-2xl p-8 text-center">
        <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
          Job not found or no longer available.
        </p>
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
          className="inline-flex items-center gap-2 mt-4 text-sm font-medium"
          style={{ color: 'var(--primary)' }}
        >
          <ArrowLeft className="w-4 h-4" />
          Back to jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
        className="inline-flex items-center gap-2 text-sm font-medium transition-colors hover:opacity-80"
        style={{ color: 'var(--neutral-gray)' }}
      >
        <ArrowLeft className="w-4 h-4" />
        Back to jobs
      </Link>

      <div className="glass-card rounded-2xl p-6 sm:p-8">
        <div className="flex items-start gap-4 mb-6">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)',
            }}
          >
            <Briefcase className="w-7 h-7" style={{ color: 'var(--primary)' }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
              {job.title}
            </h1>
            <p className="text-sm mt-1 flex items-center gap-1" style={{ color: 'var(--neutral-gray)' }}>
              <Building2 className="w-4 h-4" />
              {job.employer_name ?? 'Company'}
            </p>
            <div className="flex flex-wrap gap-3 mt-3 text-sm" style={{ color: 'var(--neutral-gray)' }}>
              {job.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {job.location}
                </span>
              )}
              {job.work_type && (
                <span className="capitalize">{job.work_type.replace('_', '-')}</span>
              )}
              {(job.salary_range || job.salary_range_min != null || job.salary_range_max != null) && (
                <span className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  {job.salary_range ||
                    (job.salary_range_min != null && job.salary_range_max != null
                      ? `${job.salary_range_min} - ${job.salary_range_max}`
                      : job.salary_range_min != null
                        ? `${job.salary_range_min}+`
                        : job.salary_range_max != null
                          ? `Up to ${job.salary_range_max}`
                          : '')}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                Posted {formatDate(job.created_at)}
              </span>
            </div>
          </div>
        </div>

        {job.description && (
          <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--neutral-border)' }}>
            <h2 className="text-sm font-semibold mb-2 flex items-center gap-2" style={{ color: 'var(--neutral-dark)' }}>
              <FileText className="w-4 h-4" />
              Description
            </h2>
            <div
              className="prose prose-sm max-w-none text-sm whitespace-pre-wrap"
              style={{ color: 'var(--neutral-gray)' }}
            >
              {job.description}
            </div>
          </div>
        )}

        {job.requirements && (
          <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--neutral-border)' }}>
            <h2 className="text-sm font-semibold mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Requirements
            </h2>
            <div
              className="text-sm whitespace-pre-wrap"
              style={{ color: 'var(--neutral-gray)' }}
            >
              {job.requirements}
            </div>
          </div>
        )}

        {job.openings_count > 0 && (
          <p className="mt-6 text-xs" style={{ color: 'var(--neutral-muted)' }}>
            {job.openings_count} position{job.openings_count !== 1 ? 's' : ''} open
          </p>
        )}
      </div>
    </div>
  );
}
