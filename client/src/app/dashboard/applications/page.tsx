'use client';

import Link from 'next/link';
import { ROUTES, WORK_TYPES } from '@/constants';
import { JOB_CARD_GRADIENTS } from '@/constants/ui';
import { useAuthStore } from '@/stores';
import { useJobs } from '@/lib/hooks';
import { formatDate } from '@/lib/utils';
import { LoadingContent } from '@/components/ui/loading-content';
import {
  Briefcase,
  ChevronRight,
  MapPin,
  Calendar,
  Users,
} from 'lucide-react';

/**
 * Application Management - Page 1: Candidates for the following jobs
 * List of published jobs; click job to see applicants
 */
export default function ApplicationsPage() {
  const employer = useAuthStore((state) => state.employer);

  const { data: jobs, isLoading } = useJobs(
    {
      employer_id: employer?.id,
      status: 'published',
    },
    undefined,
    50
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
          Application Management
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>
          Candidates for the following jobs. Click a job to view applicants.
        </p>
      </div>

      {/* Published Jobs Grid */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <LoadingContent
          isLoading={isLoading}
          isEmpty={(jobs?.items.length ?? 0) === 0}
          skeletonCount={6}
          renderSkeleton={
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="animate-pulse rounded-2xl p-5 h-40"
                  style={{
                    background: 'linear-gradient(145deg, rgba(250, 245, 255, 0.6) 0%, rgba(243, 232, 255, 0.5) 100%)',
                    border: '1px solid rgba(255, 255, 255, 0.5)',
                  }}
                >
                  <div className="w-12 h-12 rounded-xl bg-white/60 mb-3" />
                  <div className="h-4 bg-white/60 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-white/50 rounded w-1/2" />
                </div>
              ))}
            </div>
          }
          emptyContent={
            <div className="text-center py-16 px-4">
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
                }}
              >
                <Briefcase className="w-10 h-10" style={{ color: 'var(--primary)' }} />
              </div>
              <p className="text-lg font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
                No published jobs yet
              </p>
              <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                Publish a job to start receiving applications
              </p>
              <Link
                href={ROUTES.JOBS}
                className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium mt-4"
              >
                View Jobs
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          }
        >
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {jobs?.items.map((job, index) => {
              const cardStyle = JOB_CARD_GRADIENTS[index % JOB_CARD_GRADIENTS.length];
              return (
                <Link
                  key={job.id}
                  href={ROUTES.APPLICATIONS_JOB(job.id)}
                  className="flex flex-col rounded-2xl p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg"
                  style={{
                    background: cardStyle.bg,
                    backdropFilter: 'blur(16px)',
                    WebkitBackdropFilter: 'blur(16px)',
                    border: cardStyle.border,
                    boxShadow: cardStyle.shadow,
                  }}
                >
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center mb-3 flex-shrink-0"
                    style={{ background: cardStyle.iconBg }}
                  >
                    <Briefcase className="w-6 h-6" style={{ color: cardStyle.accent }} />
                  </div>

                  <h3 className="text-base font-semibold truncate mb-1" style={{ color: 'var(--neutral-dark)' }}>
                    {job.title}
                  </h3>

                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-auto text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                        {job.location}
                      </span>
                    )}
                    {job.work_type && (
                      <span className="hidden sm:inline">
                        {WORK_TYPES.find((t) => t.value === job.work_type)?.label}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 flex-shrink-0" />
                      {formatDate(job.created_at)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-3" style={{ borderTop: '1px solid rgba(124, 58, 237, 0.1)' }}>
                    <span className="flex items-center gap-1.5 text-xs font-medium" style={{ color: cardStyle.accent }}>
                      <Users className="w-4 h-4" />
                      View applicants
                    </span>
                    <ChevronRight className="w-5 h-5" style={{ color: cardStyle.accent }} />
                  </div>
                </Link>
              );
            })}
          </div>
        </LoadingContent>
      </div>
    </div>
  );
}
