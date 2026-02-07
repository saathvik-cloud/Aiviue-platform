'use client';

/**
 * Candidate Jobs Page - Job Recommendations
 *
 * Lists published jobs with optional matching by candidate's preferred
 * category and location. Gradient + glass cards aligned with employer module.
 */

import { ROUTES } from '@/constants';
import { useJobs } from '@/lib/hooks';
import { useCandidateAuthStore } from '@/stores';
import { formatDate, getCurrencySymbol } from '@/lib/utils';
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

// Gradient card styles (rotate per card for variety, employer-style)
const CARD_GRADIENTS = [
  {
    bg: 'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.9) 50%, rgba(237, 233, 254, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
    accent: '#7C3AED',
    iconBg: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(240, 253, 250, 0.98) 0%, rgba(220, 245, 238, 0.9) 50%, rgba(204, 251, 241, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(20, 184, 166, 0.1), inset 0 1px 0 rgba(255,255,255,0.5)',
    accent: '#14B8A6',
    iconBg: 'linear-gradient(135deg, rgba(20, 184, 166, 0.15) 0%, rgba(45, 212, 191, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(255, 251, 243, 0.98) 0%, rgba(254, 243, 219, 0.9) 50%, rgba(253, 230, 198, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(245, 158, 11, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
    accent: '#D97706',
    iconBg: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(251, 191, 36, 0.12) 100%)',
  },
] as const;

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
          {showAll
            ? 'All published jobs'
            : hasFilters
              ? 'Jobs matching your profile'
              : 'Complete your profile to get better matches'}
        </p>
      </div>

      {/* Tabs: For You / Explore All Jobs */}
      {hasFilters && (
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={() => setShowAll(false)}
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              !showAll ? 'text-white shadow-md' : 'btn-glass'
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
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              showAll ? 'text-white shadow-md' : 'btn-glass'
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

      {/* Job cards grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="rounded-2xl p-5 animate-pulse relative overflow-hidden"
              style={{
                background: CARD_GRADIENTS[i % 3].bg,
                border: CARD_GRADIENTS[i % 3].border,
                boxShadow: CARD_GRADIENTS[i % 3].shadow,
                backdropFilter: 'blur(16px)',
              }}
            >
              <div className="h-5 rounded w-3/4 mb-3" style={{ background: 'rgba(124, 58, 237, 0.1)' }} />
              <div className="h-4 rounded w-1/2 mb-2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
              <div className="h-4 rounded w-1/3" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
            </div>
          ))}
        </div>
      ) : !hasMatches ? (
        <div
          className="glass-card rounded-2xl p-8 sm:p-10 text-center"
          style={{ maxWidth: '28rem', margin: '0 auto' }}
        >
          <div
            className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4"
            style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(20, 184, 166, 0.15) 100%)',
            }}
          >
            <Briefcase className="w-10 h-10" style={{ color: 'var(--primary)' }} />
          </div>
          <h3 className="text-lg font-bold mb-2" style={{ color: 'var(--neutral-dark)' }}>
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
              className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold"
            >
              <Sparkles className="w-4 h-4" />
              Explore All Jobs
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {items.map((job, index) => {
            const style = CARD_GRADIENTS[index % CARD_GRADIENTS.length];
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
                      {getCurrencySymbol(job.currency)} {job.salary_range}
                    </p>
                  )}
                  <p className="flex items-center gap-2 text-xs font-medium" style={{ color: '#6B7280' }}>
                    <Clock className="w-3.5 h-3.5" style={{ color: style.accent }} />
                    {formatDate(job.created_at)}
                    {job.openings_count > 1 && ` · ${job.openings_count} openings`}
                  </p>
                </div>

                <div className="mt-4 pt-4" style={{ borderTop: '1px solid rgba(124, 58, 237, 0.15)' }}>
                  <Link
                    href={`/candidate/dashboard/jobs/${job.id}`}
                    className="inline-flex items-center gap-1.5 text-sm font-semibold transition-all hover:opacity-90"
                    style={{ color: style.accent }}
                  >
                    View details
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
