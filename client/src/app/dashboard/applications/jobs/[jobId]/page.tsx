'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ROUTES } from '@/constants';
import { useJob, useApplicationsForJob } from '@/lib/hooks';
import { formatDate } from '@/lib/utils';
import { LoadingContent } from '@/components/ui/loading-content';
import {
  ArrowLeft,
  Briefcase,
  ChevronRight,
  FileText,
  User,
  Users,
} from 'lucide-react';

/**
 * Application Management - Page 2: List applicants for a job
 */
export default function JobApplicantsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;

  const { data: job, isLoading: jobLoading } = useJob(jobId);
  const { data: applications, isLoading: appsLoading } = useApplicationsForJob(jobId);

  const isLoading = jobLoading || appsLoading;

  if (!jobLoading && job === undefined) {
    router.replace(ROUTES.APPLICATIONS);
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={ROUTES.APPLICATIONS}
        className="inline-flex items-center gap-2 text-sm font-medium transition-colors hover:opacity-80"
        style={{ color: 'var(--primary)' }}
      >
        <ArrowLeft className="w-4 h-4" />
        Back to jobs
      </Link>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
          {job?.title ?? 'Applicants'}
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>
          {applications?.items.length ?? 0} applicant
          {(applications?.items.length ?? 0) !== 1 ? 's' : ''} for this job
        </p>
      </div>

      {/* Applicants List */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <LoadingContent
          isLoading={isLoading}
          isEmpty={(applications?.items.length ?? 0) === 0}
          skeletonCount={5}
          renderSkeleton={
            <div className="p-5 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="animate-pulse flex items-center gap-4 p-4 rounded-xl bg-white/50"
                >
                  <div className="w-12 h-12 rounded-full bg-gray-200" />
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-1/3 mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-1/4" />
                  </div>
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
                <Users className="w-10 h-10" style={{ color: 'var(--primary)' }} />
              </div>
              <p className="text-lg font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
                No applicants yet
              </p>
              <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                Candidates will appear here when they apply
              </p>
              <Link
                href={ROUTES.APPLICATIONS}
                className="btn-glass inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium mt-4"
                style={{ color: 'var(--primary)' }}
              >
                Back to jobs
              </Link>
            </div>
          }
        >
          <div className="divide-y" style={{ borderColor: 'rgba(226, 232, 240, 0.5)' }}>
            {applications?.items.map((app) => (
              <Link
                key={app.id}
                href={ROUTES.APPLICATIONS_JOB_CANDIDATE(jobId, app.id)}
                className="flex items-center gap-4 p-5 transition-all hover:bg-white/80"
              >
                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{
                    background:
                      'linear-gradient(135deg, rgba(124, 58, 237, 0.12) 0%, rgba(236, 72, 153, 0.1) 100%)',
                  }}
                >
                  <User className="w-6 h-6" style={{ color: 'var(--primary)' }} />
                </div>

                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold truncate" style={{ color: 'var(--neutral-dark)' }}>
                    {app.candidate_name}
                  </h3>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    {app.role_name && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="w-3.5 h-3.5" />
                        {app.role_name}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <span>Applied</span>
                      {formatDate(app.applied_at)}
                    </span>
                    {app.has_resume_pdf && (
                      <span className="flex items-center gap-1" style={{ color: 'var(--status-published)' }}>
                        <FileText className="w-3.5 h-3.5" />
                        Resume
                      </span>
                    )}
                  </div>
                </div>

                <ChevronRight className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--neutral-muted)' }} />
              </Link>
            ))}
          </div>
        </LoadingContent>
      </div>
    </div>
  );
}
