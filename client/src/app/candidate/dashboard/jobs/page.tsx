'use client';

/**
 * Candidate Jobs Page - Job Recommendations
 *
 * Lists published jobs with optional matching by candidate's preferred
 * category and location. Glassmorphism cards, same UI principles as employer module.
 * "Explore more jobs" when no filters or no matches.
 */

import { ROUTES } from '@/constants';
import { useJobs } from '@/lib/hooks';
import { useCandidateAuthStore } from '@/stores';
import { formatDate } from '@/lib/utils';
import {
  Briefcase,
  MapPin,
  ArrowRight,
  Sparkles,
  Building2,
  Clock,
  DollarSign,
} from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';

const RECOMMENDED_LIMIT = 12;

export default function CandidateJobsPage() {
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const [showAll, setShowAll] = useState(false);

  // Build filters: prefer candidate's category/location when "recommended", else show all published
  const filters = useMemo(() => {
    const base: Parameters<typeof useJobs>[0] = { status: 'published' };
    if (!showAll && candidate?.preferred_job_category_id) {
      base.category_id = candidate.preferred_job_category_id;
    }
    // Optional: match by location (backend has city/state; candidate has preferred_job_location string)
    if (!showAll && candidate?.preferred_job_location) {
      const loc = candidate.preferred_job_location.trim();
      if (loc) base.city = loc;
    }
    return base;
  }, [showAll, candidate?.preferred_job_category_id, candidate?.preferred_job_location]);

  const { data: jobList, isLoading } = useJobs(filters, undefined, RECOMMENDED_LIMIT);
  const items = jobList?.items ?? [];
  const hasMatches = items.length > 0;
  const hasFilters = !!(candidate?.preferred_job_category_id || candidate?.preferred_job_location);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1
          className="text-2xl sm:text-3xl font-bold"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Job Recommendations
        </h1>
        <p className="text-sm sm:text-base mt-1" style={{ color: 'var(--neutral-gray)' }}>
          {showAll
            ? 'All published jobs'
            : hasFilters
              ? 'Jobs matching your profile'
              : 'Complete your profile to get better matches'}
        </p>
      </div>

      {/* Explore / Show recommended toggle */}
      {hasFilters && (
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setShowAll(false)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              !showAll ? 'text-white' : 'btn-glass'
            }`}
            style={
              !showAll
                ? { background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }
                : { color: 'var(--neutral-dark)' }
            }
          >
            For You
          </button>
          <button
            type="button"
            onClick={() => setShowAll(true)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              showAll ? 'text-white' : 'btn-glass'
            }`}
            style={
              showAll
                ? { background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }
                : { color: 'var(--neutral-dark)' }
            }
          >
            Explore All Jobs
          </button>
        </div>
      )}

      {/* Job List */}
      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="glass-card rounded-2xl p-5 animate-pulse"
            >
              <div className="h-5 rounded w-3/4 mb-3" style={{ background: 'var(--neutral-light)' }} />
              <div className="h-4 rounded w-1/2 mb-2" style={{ background: 'var(--neutral-light)' }} />
              <div className="h-4 rounded w-1/3" style={{ background: 'var(--neutral-light)' }} />
            </div>
          ))}
        </div>
      ) : !hasMatches ? (
        <div className="glass-card rounded-2xl p-10 text-center">
          <div
            className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4"
            style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)',
            }}
          >
            <Briefcase className="w-10 h-10" style={{ color: 'var(--primary)' }} />
          </div>
          <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--neutral-dark)' }}>
            {showAll ? 'No jobs published yet' : 'No matching jobs right now'}
          </h3>
          <p className="text-sm mb-6" style={{ color: 'var(--neutral-gray)' }}>
            {showAll
              ? 'Check back later for new opportunities.'
              : 'Try "Explore All Jobs" or complete your profile (category & location) for better recommendations.'}
          </p>
          {hasFilters && !showAll && (
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white"
              style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)' }}
            >
              <Sparkles className="w-4 h-4" />
              Explore All Jobs
            </button>
          )}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((job) => (
            <div
              key={job.id}
              className="glass-card rounded-2xl p-5 transition-all hover:shadow-lg hover:scale-[1.02] flex flex-col"
            >
              <div className="flex items-start gap-3 mb-3">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{
                    background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)',
                  }}
                >
                  <Briefcase className="w-6 h-6" style={{ color: 'var(--primary)' }} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-semibold truncate" style={{ color: 'var(--neutral-dark)' }}>
                    {job.title}
                  </h3>
                  <p className="text-xs mt-0.5 flex items-center gap-1 truncate" style={{ color: 'var(--neutral-gray)' }}>
                    <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
                    {job.employer_name ?? 'Company'}
                  </p>
                </div>
              </div>

              <div className="space-y-2 mt-2 flex-1">
                {job.location && (
                  <p className="flex items-center gap-2 text-sm" style={{ color: 'var(--neutral-gray)' }}>
                    <MapPin className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{job.location}</span>
                  </p>
                )}
                {job.salary_range && (
                  <p className="flex items-center gap-2 text-sm" style={{ color: 'var(--neutral-gray)' }}>
                    <DollarSign className="w-4 h-4 flex-shrink-0" />
                    {job.salary_range}
                  </p>
                )}
                <p className="flex items-center gap-2 text-xs" style={{ color: 'var(--neutral-muted)' }}>
                  <Clock className="w-3.5 h-3.5" />
                  {formatDate(job.created_at)}
                  {job.openings_count > 1 && ` · ${job.openings_count} openings`}
                </p>
              </div>

              <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--neutral-border)' }}>
                <Link
                  href={`/candidate/dashboard/jobs/${job.id}`}
                  className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-90"
                  style={{ color: 'var(--primary)' }}
                >
                  View details
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
