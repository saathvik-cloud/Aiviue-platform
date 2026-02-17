'use client';

/**
 * Candidate Jobs Page - Job Recommendations + Applied Jobs
 *
 * Lists published jobs with optional matching by candidate's preferred
 * category and location. Tab: For You / Explore All Jobs / Applied Jobs.
 * Gradient + glass cards aligned with employer module.
 */

import { LoadingContent } from '@/components/ui/loading-content';
import { ApplyWithResumeModal } from '@/components/apply-with-resume-modal';
import { JOB_CARD_GRADIENTS } from '@/constants';
import { useJobs, useAppliedJobIds, useAppliedJobsList } from '@/lib/hooks';
import { useCandidateAuthStore } from '@/stores';
import { formatDate, getCurrencySymbol, stripSalaryRangeCurrency } from '@/lib/utils';
import {
  Briefcase,
  MapPin,
  ArrowRight,
  Sparkles,
  Building2,
  Clock,
  DollarSign,
  CheckCircle,
  Send,
} from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { applicationKeys } from '@/lib/hooks/use-applications';
import type { JobSummary } from '@/types';

const RECOMMENDED_LIMIT = 12;
const APPLIED_PAGE_SIZE = 20;
type Tab = 'forYou' | 'exploreAll' | 'appliedJobs';

export default function CandidateJobsPage() {
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>('forYou');
  const [applyModalJob, setApplyModalJob] = useState<{ id: string; title: string } | null>(null);

  // Applied jobs: accumulate pages when "Load more" is used
  const [appliedItems, setAppliedItems] = useState<JobSummary[]>([]);
  const [appliedNextCursor, setAppliedNextCursor] = useState<string | null>(null);
  const [appliedLoadCursor, setAppliedLoadCursor] = useState<string | undefined>(undefined);

  const { data: appliedJobsData } = useAppliedJobIds(candidate?.id);
  const appliedJobIds = new Set(appliedJobsData?.job_ids ?? []);

  const { data: appliedPageData, isLoading: appliedLoading } = useAppliedJobsList(
    candidate?.id,
    appliedLoadCursor ?? undefined,
    APPLIED_PAGE_SIZE
  );

  // When switching to Applied tab: reset state and refetch so we show fresh data (fixes stale empty cache)
  useEffect(() => {
    if (tab === 'appliedJobs') {
      setAppliedItems([]);
      setAppliedNextCursor(null);
      setAppliedLoadCursor(undefined);
      queryClient.refetchQueries({ queryKey: applicationKeys.appliedJobsList });
    }
  }, [tab, queryClient]);

  // Sync applied list from API: first page overwrites; load-more appends
  useEffect(() => {
    if (tab !== 'appliedJobs' || !appliedPageData) return;
    if (appliedLoadCursor === undefined) {
      setAppliedItems((prev) => (prev.length === 0 ? appliedPageData.items : prev));
      setAppliedNextCursor(appliedPageData.next_cursor);
    } else {
      setAppliedItems((prev) => [...prev, ...appliedPageData.items]);
      setAppliedNextCursor(appliedPageData.next_cursor);
      setAppliedLoadCursor(undefined);
    }
  }, [tab, appliedPageData, appliedLoadCursor]);

  const showAll = tab === 'exploreAll';
  const filters = useMemo(() => {
    const base: Parameters<typeof useJobs>[0] = { status: 'published' };
    if (tab === 'forYou' && candidate?.preferred_job_category_id) {
      base.category_id = candidate.preferred_job_category_id;
    }
    if (tab === 'forYou' && candidate?.preferred_job_location) {
      const loc = candidate.preferred_job_location.trim();
      if (loc) base.city = loc;
    }
    return base;
  }, [tab, candidate?.preferred_job_category_id, candidate?.preferred_job_location]);

  const { data: jobList, isLoading: jobsLoading } = useJobs(filters, undefined, RECOMMENDED_LIMIT);
  const recommendationItems = jobList?.items ?? [];
  const hasFilters = !!(candidate?.preferred_job_category_id || candidate?.preferred_job_location);

  const isAppliedTab = tab === 'appliedJobs';
  const items = isAppliedTab ? appliedItems : recommendationItems;
  const isLoading = isAppliedTab ? appliedLoading : jobsLoading;
  const hasMatches = items.length > 0;
  const appliedHasMore = isAppliedTab && appliedNextCursor != null;

  return (
    <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 space-y-5 sm:space-y-6 pb-8">
      {/* Page Header */}
      <div>
        <h1
          className="text-xl sm:text-2xl lg:text-3xl font-bold"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Job Recommendations
        </h1>
        <p className="text-sm sm:text-base mt-1" style={{ color: 'var(--neutral-gray)' }}>
          {isAppliedTab
            ? 'Jobs you have applied to'
            : showAll
              ? 'All published jobs'
              : hasFilters
                ? 'Jobs matching your profile'
                : 'Complete your profile to get better matches'}
        </p>
      </div>

      {/* Tabs: For You / Explore All Jobs / Applied Jobs */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {hasFilters && (
          <>
            <button
              type="button"
              onClick={() => setTab('forYou')}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                tab === 'forYou' ? 'text-white shadow-md' : 'btn-glass'
              }`}
              style={
                tab === 'forYou'
                  ? { background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }
                  : { color: 'var(--neutral-dark)' }
              }
            >
              For You
            </button>
            <button
              type="button"
              onClick={() => setTab('exploreAll')}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                tab === 'exploreAll' ? 'text-white shadow-md' : 'btn-glass'
              }`}
              style={
                tab === 'exploreAll'
                  ? { background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }
                  : { color: 'var(--neutral-dark)' }
              }
            >
              Explore All Jobs
            </button>
          </>
        )}
        {!hasFilters && (
          <button
            type="button"
            onClick={() => setTab('exploreAll')}
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              tab === 'exploreAll' ? 'text-white shadow-md' : 'btn-glass'
            }`}
            style={
              tab === 'exploreAll'
                ? { background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }
                : { color: 'var(--neutral-dark)' }
            }
          >
            Explore All Jobs
          </button>
        )}
        <button
          type="button"
          onClick={() => setTab('appliedJobs')}
          className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            tab === 'appliedJobs' ? 'text-white shadow-md' : 'btn-glass'
          }`}
          style={
            tab === 'appliedJobs'
              ? { background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }
              : { color: 'var(--neutral-dark)' }
          }
        >
          Applied Jobs
        </button>
      </div>

      {/* Job cards grid */}
      <LoadingContent
        isLoading={isLoading}
        isEmpty={!hasMatches}
        renderSkeleton={
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="rounded-2xl p-5 animate-pulse relative overflow-hidden"
                style={{
                  background: JOB_CARD_GRADIENTS[i % JOB_CARD_GRADIENTS.length].bg,
                  border: JOB_CARD_GRADIENTS[i % JOB_CARD_GRADIENTS.length].border,
                  boxShadow: JOB_CARD_GRADIENTS[i % JOB_CARD_GRADIENTS.length].shadow,
                  backdropFilter: 'blur(16px)',
                }}
              >
                <div className="h-5 rounded w-3/4 mb-3" style={{ background: 'rgba(124, 58, 237, 0.1)' }} />
                <div className="h-4 rounded w-1/2 mb-2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
                <div className="h-4 rounded w-1/3" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
              </div>
            ))}
          </div>
        }
        emptyContent={
          <div className="glass-card rounded-2xl p-8 sm:p-10 text-center" style={{ maxWidth: '28rem', margin: '0 auto' }}>
            <div
              className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(20, 184, 166, 0.15) 100%)' }}
            >
              <Briefcase className="w-10 h-10" style={{ color: 'var(--primary)' }} />
            </div>
            <h3 className="text-lg font-bold mb-2" style={{ color: 'var(--neutral-dark)' }}>
              {isAppliedTab
                ? 'No applied jobs yet'
                : showAll
                  ? 'No jobs published yet'
                  : 'No matching jobs right now'}
            </h3>
            <p className="text-sm mb-6" style={{ color: 'var(--neutral-gray)' }}>
              {isAppliedTab
                ? 'Apply to jobs from For You or Explore All Jobs to see them here.'
                : showAll
                  ? 'Check back later for new opportunities.'
                  : 'Try "Explore All Jobs" or complete your profile (category & location) for better recommendations.'}
            </p>
            {hasFilters && tab === 'forYou' && (
              <button
                type="button"
                onClick={() => setTab('exploreAll')}
                className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold"
              >
                <Sparkles className="w-4 h-4" />
                Explore All Jobs
              </button>
            )}
            {isAppliedTab && (
              <button
                type="button"
                onClick={() => setTab(hasFilters ? 'forYou' : 'exploreAll')}
                className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold"
              >
                <Sparkles className="w-4 h-4" />
                Browse jobs
              </button>
            )}
          </div>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {items.map((job, index) => {
            const style = JOB_CARD_GRADIENTS[index % JOB_CARD_GRADIENTS.length];
            return (
              <div
                key={job.id}
                className="rounded-2xl p-5 relative overflow-hidden flex flex-col transition-all hover:scale-[1.02] hover:shadow-xl"
                style={{
                  background: style.bg,
                  border: style.border,
                  boxShadow: style.shadow,
                  backdropFilter: 'blur(16px)',
                }}
              >
                <div className="flex items-start gap-3 mb-3">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: style.iconBg }}
                  >
                    <Briefcase className="w-6 h-6" style={{ color: style.accent }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold truncate" style={{ color: '#374151' }}>
                      {job.title}
                    </h3>
                    <p className="text-xs mt-0.5 flex items-center gap-1 truncate font-medium" style={{ color: '#6B7280' }}>
                      <Building2 className="w-3.5 h-3.5 flex-shrink-0" style={{ color: style.accent }} />
                      {job.employer_name ?? 'Company'}
                    </p>
                  </div>
                </div>

                <div className="space-y-2 mt-2 flex-1">
                  {job.location && (
                    <p className="flex items-center gap-2 text-sm font-medium" style={{ color: '#4B5563' }}>
                      <MapPin className="w-4 h-4 flex-shrink-0" style={{ color: style.accent }} />
                      <span className="truncate">{job.location}</span>
                    </p>
                  )}
                  {job.salary_range && (
                    <p className="flex items-center gap-2 text-sm font-medium" style={{ color: '#4B5563' }}>
                      <DollarSign className="w-4 h-4 flex-shrink-0" style={{ color: style.accent }} />
                      {getCurrencySymbol(job.currency)} {stripSalaryRangeCurrency(job.salary_range)}
                    </p>
                  )}
                  <p className="flex items-center gap-2 text-xs font-medium" style={{ color: '#6B7280' }}>
                    <Clock className="w-3.5 h-3.5" style={{ color: style.accent }} />
                    {formatDate(job.created_at)}
                    {job.openings_count > 1 && ` · ${job.openings_count} openings`}
                  </p>
                </div>

                <div
                  className="mt-4 pt-4 flex flex-wrap items-center gap-2"
                  style={{ borderTop: '1px solid rgba(124, 58, 237, 0.15)' }}
                >
                  <Link
                    href={`/candidate/dashboard/jobs/${job.id}`}
                    className="inline-flex items-center gap-1.5 text-sm font-semibold transition-all hover:opacity-90"
                    style={{ color: style.accent }}
                  >
                    View details
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                  {isAppliedTab || appliedJobIds.has(job.id) ? (
                    <span
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{
                        background: 'rgba(34, 197, 94, 0.15)',
                        color: 'var(--status-published)',
                      }}
                    >
                      <CheckCircle className="w-4 h-4" />
                      Applied
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        setApplyModalJob({ id: job.id, title: job.title });
                      }}
                      className="btn-gradient inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                    >
                      <Send className="w-4 h-4" />
                      Apply
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </LoadingContent>

      {/* Load more for Applied Jobs */}
      {isAppliedTab && hasMatches && appliedHasMore && (
        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={() => setAppliedLoadCursor(appliedNextCursor)}
            disabled={appliedLoading}
            className="btn-glass px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-60"
            style={{ color: 'var(--neutral-dark)' }}
          >
            {appliedLoading ? 'Loading…' : 'Load more'}
          </button>
        </div>
      )}

      <ApplyWithResumeModal
        open={!!applyModalJob}
        onOpenChange={(open) => !open && setApplyModalJob(null)}
        jobId={applyModalJob?.id ?? ''}
        jobTitle={applyModalJob?.title}
        onSuccess={() => setApplyModalJob(null)}
      />
    </div>
  );
}
