'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { ROUTES } from '@/constants';
import { useCandidateResumes, useJobs } from '@/lib/hooks';
import { formatDate, getCurrencySymbol, stripSalaryRangeCurrency } from '@/lib/utils';
import { useCandidateAuthStore } from '@/stores';
import {
  ArrowRight,
  Briefcase,
  Building2,
  CheckCircle,
  Clock,
  DollarSign,
  FileText,
  History,
  MapPin,
  Sparkles,
  User
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { useMemo } from 'react';

// Faded background for Recommended Jobs tile (when carousel is shown). Lazy-loaded.
const RECOMMENDED_JOBS_TILE_BG_IMAGE =
  'https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=800&q=80';

/**
 * Candidate Dashboard Home Page
 *
 * Shows welcome message, profile completion status, quick actions,
 * and a placeholder for job recommendations (Step 3.8).
 */
const RECOMMENDED_JOBS_CAROUSEL_LIMIT = 8;

export default function CandidateDashboardPage() {
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const { data: resumes } = useCandidateResumes(candidate?.id);

  // "Has resume" = at least one resume built/uploaded in AIVI (not just profile complete)
  const hasResume = (resumes?.length ?? 0) > 0;

  // Recommended jobs for carousel (only fetched when user has resume)
  const jobFilters = useMemo(() => {
    const base: { status: 'published'; category_id?: string; city?: string } = { status: 'published' };
    if (candidate?.preferred_job_category_id) base.category_id = candidate.preferred_job_category_id;
    if (candidate?.preferred_job_location?.trim()) base.city = candidate.preferred_job_location.trim();
    return base;
  }, [candidate]);
  const { data: jobList, isLoading: jobsLoading } = useJobs(
    jobFilters,
    undefined,
    RECOMMENDED_JOBS_CAROUSEL_LIMIT
  );
  const recommendedJobs = jobList?.items ?? [];

  // Profile completion calculation
  const profileFields = [
    candidate?.name,
    candidate?.email,
    candidate?.current_location,
    candidate?.preferred_job_category_id,
    candidate?.preferred_job_role_id,
    candidate?.date_of_birth,
    candidate?.languages_known?.length,
    candidate?.about,
  ];
  const filledFields = profileFields.filter(Boolean).length;
  const profileCompletion = Math.round((filledFields / profileFields.length) * 100);

  // Distinct soft gradients per tile (not solid – pink/violet, purple, amber/yellow, teal)
  const statCards = [
    {
      label: 'Profile',
      value: `${profileCompletion}%`,
      sublabel: profileCompletion === 100 ? 'Complete' : 'Incomplete',
      icon: User,
      cardBg:
        'linear-gradient(145deg, rgba(253, 242, 248, 0.95) 0%, rgba(251, 207, 232, 0.4) 50%, rgba(243, 232, 255, 0.5) 100%)',
      gradient: 'linear-gradient(135deg, #EC4899 0%, #A78BFA 100%)',
      bgLight: 'rgba(236, 72, 153, 0.15)',
      iconColor: '#DB2777',
    },
    {
      label: 'Resume',
      value: (resumes?.length ?? 0) > 0 ? '1' : '0',
      sublabel: 'Active resume',
      icon: FileText,
      cardBg:
        'linear-gradient(145deg, rgba(245, 243, 255, 0.98) 0%, rgba(237, 233, 254, 0.6) 50%, rgba(221, 214, 254, 0.4) 100%)',
      gradient: 'linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%)',
      bgLight: 'rgba(124, 58, 237, 0.15)',
      iconColor: 'var(--primary)',
    },
    {
      label: 'Job Matches',
      value: '--',
      sublabel: 'Coming soon',
      icon: Briefcase,
      cardBg:
        'linear-gradient(145deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.5) 50%, rgba(253, 230, 138, 0.3) 100%)',
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #FCD34D 100%)',
      bgLight: 'rgba(245, 158, 11, 0.2)',
      iconColor: '#D97706',
    },
    {
      label: 'Applications',
      value: '0',
      sublabel: 'Applied jobs',
      icon: CheckCircle,
      cardBg:
        'linear-gradient(145deg, rgba(240, 253, 250, 0.95) 0%, rgba(204, 251, 241, 0.5) 50%, rgba(167, 243, 208, 0.3) 100%)',
      gradient: 'linear-gradient(135deg, #14B8A6 0%, #5EEAD4 100%)',
      bgLight: 'rgba(20, 184, 166, 0.15)',
      iconColor: 'var(--secondary-teal)',
    },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto space-y-4 sm:space-y-6">
      {/* Welcome Header */}
      <div>
        <h1
          className="text-xl sm:text-2xl lg:text-3xl font-bold"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Welcome, {candidate?.name?.split(' ')[0] || 'there'}!
        </h1>
        <p
          className="text-sm sm:text-base mt-1"
          style={{ color: 'var(--neutral-gray)' }}
        >
          Build your resume and discover jobs that match your skills
        </p>
      </div>

      {/* Stats Cards – each with distinct soft gradient */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="rounded-2xl p-4 sm:p-5 relative overflow-hidden transition-all hover:scale-[1.02] hover:shadow-lg"
              style={{
                background: stat.cardBg,
                border: '1px solid rgba(255, 255, 255, 0.7)',
                boxShadow: '0 4px 20px rgba(0,0,0,0.04)',
              }}
            >
              <div
                className="absolute top-0 right-0 w-20 h-20 sm:w-24 sm:h-24 rounded-full opacity-20 blur-2xl transform translate-x-6 -translate-y-6"
                style={{ background: stat.gradient }}
              />
              <div className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center"
                    style={{ background: stat.bgLight }}
                  >
                    <Icon className="w-5 h-5" style={{ color: stat.iconColor }} />
                  </div>
                </div>
                <p
                  className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-1"
                  style={{ color: 'var(--neutral-dark)' }}
                >
                  {stat.value}
                </p>
                <p className="text-xs sm:text-sm" style={{ color: 'var(--neutral-gray)' }}>
                  {stat.sublabel}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Quick Actions – each card with distinct soft gradient */}
        <div className="lg:col-span-1">
          <div
            className="rounded-2xl p-4 sm:p-5 h-full"
            style={{
              background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.9) 0%, rgba(253, 242, 248, 0.4) 50%, rgba(243, 232, 255, 0.3) 100%)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.7)',
              boxShadow: '0 4px 24px rgba(124, 58, 237, 0.06)',
            }}
          >
            <h2
              className="text-base font-semibold mb-3 sm:mb-4"
              style={{ color: 'var(--neutral-dark)' }}
            >
              Quick Actions
            </h2>
            <div className="space-y-2 sm:space-y-3">
              {/* Build Resume – pink / light violet */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_RESUME}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02]"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(253, 242, 248, 0.9) 0%, rgba(243, 232, 255, 0.7) 50%, rgba(221, 214, 254, 0.5) 100%)',
                  border: '1px solid rgba(236, 72, 153, 0.15)',
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{
                    background: 'linear-gradient(135deg, #EC4899 0%, #7C3AED 100%)',
                  }}
                >
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--neutral-dark)' }}>
                    Build Resume with AIVI
                  </p>
                  <p className="text-xs truncate" style={{ color: 'var(--neutral-gray)' }}>
                    AI-powered resume builder
                  </p>
                </div>
              </Link>

              {/* Browse Jobs – light purple / slate */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02]"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(245, 243, 255, 0.9) 0%, rgba(237, 233, 254, 0.6) 50%, rgba(226, 232, 240, 0.4) 100%)',
                  border: '1px solid rgba(124, 58, 237, 0.12)',
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)' }}
                >
                  <Briefcase className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--neutral-dark)' }}>
                    Browse Jobs
                  </p>
                  <p className="text-xs truncate" style={{ color: 'var(--neutral-gray)' }}>
                    Find matching opportunities
                  </p>
                </div>
              </Link>

              {/* Update Profile – light yellow / amber */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_PROFILE}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02]"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(255, 251, 235, 0.9) 0%, rgba(254, 243, 199, 0.5) 50%, rgba(253, 230, 138, 0.25) 100%)',
                  border: '1px solid rgba(245, 158, 11, 0.15)',
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(234, 179, 8, 0.2) 100%)' }}
                >
                  <User className="w-5 h-5" style={{ color: '#D97706' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--neutral-dark)' }}>
                    Update Profile
                  </p>
                  <p className="text-xs truncate" style={{ color: 'var(--neutral-gray)' }}>
                    Complete your details
                  </p>
                </div>
              </Link>

              {/* Resume History – light orange / peach */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_RESUME_HISTORY}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02]"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(255, 247, 237, 0.9) 0%, rgba(254, 215, 170, 0.4) 50%, rgba(251, 191, 36, 0.2) 100%)',
                  border: '1px solid rgba(249, 115, 22, 0.15)',
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(251, 146, 60, 0.2) 100%)' }}
                >
                  <History className="w-5 h-5" style={{ color: '#EA580C' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--neutral-dark)' }}>
                    Resume History
                  </p>
                  <p className="text-xs truncate" style={{ color: 'var(--neutral-gray)' }}>
                    View and download past resumes
                  </p>
                </div>
              </Link>
            </div>
          </div>
        </div>

        {/* Job Recommendations – soft purple/pink gradient; when hasResume, faded BG image behind carousel */}
        <div className="lg:col-span-2">
          <div
            className="rounded-2xl p-4 sm:p-5 relative overflow-hidden"
            style={{
              background:
                'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.6) 50%, rgba(253, 242, 248, 0.4) 100%)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.7)',
              boxShadow: '0 4px 24px rgba(124, 58, 237, 0.08)',
            }}
          >
            {/* Faded background image (lazy-loaded) – only when showing carousel */}
            {hasResume && (
              <Image
                src={RECOMMENDED_JOBS_TILE_BG_IMAGE}
                alt=""
                fill
                sizes="(max-width: 1024px) 100vw, 66vw"
                className="object-cover opacity-[0.7] pointer-events-none select-none"
                style={{ zIndex: 0 }}
                placeholder="blur"
                blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAIAAoDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAAAAUH/8QAIhAAAgEDBAMBAAAAAAAAAAAAAQIDAAQRBRIhMQYTQVFh/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAZEQACAwEAAAAAAAAAAAAAAAABAgADESH/2gAMAwEAAhEDEEA/AN+iiirnMZ//2Q=="
              />
            )}
            <div
              className="absolute top-0 right-0 w-32 h-32 opacity-20 blur-3xl pointer-events-none"
              style={{ background: 'radial-gradient(circle, rgba(236, 72, 153, 0.4) 0%, rgba(124, 58, 237, 0.3) 50%, transparent 70%)', zIndex: 1 }}
            />
            <div className="relative z-10">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <h2 className="text-base font-semibold" style={{ color: 'var(--neutral-dark)' }}>
                Recommended Jobs
              </h2>
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
                className="text-sm font-medium flex items-center gap-1 transition-colors hover:opacity-80"
                style={{ color: 'var(--primary)' }}
              >
                View all
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* No resume: show CTA. Has resume: show job carousel */}
            {!hasResume ? (
              <div className="relative text-center py-8 sm:py-10">
                <div
                  className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center mx-auto mb-3 sm:mb-4"
                  style={{
                    background:
                      'linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(124, 58, 237, 0.15) 100%)',
                  }}
                >
                  <Briefcase className="w-7 h-7 sm:w-8 sm:h-8" style={{ color: 'var(--primary)' }} />
                </div>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
                  Build your resume first
                </p>
                <p className="text-xs mb-4 px-2" style={{ color: 'var(--neutral-gray)' }}>
                  Complete your resume to get personalized job recommendations
                </p>
                <Link
                  href={ROUTES.CANDIDATE_DASHBOARD_RESUME}
                  className="btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
                >
                  <Sparkles className="w-4 h-4" />
                  Build Resume
                </Link>
              </div>
            ) : jobsLoading ? (
              <div className="relative flex gap-3 overflow-x-auto overflow-y-hidden py-2 -mx-1 px-1 snap-x snap-mandatory scrollbar-thin">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="flex-shrink-0 w-[260px] sm:w-[280px] rounded-xl p-4 border border-white/70 snap-center"
                    style={{
                      background: 'linear-gradient(145deg, rgba(245, 243, 255, 0.9) 0%, rgba(237, 233, 254, 0.6) 100%)',
                    }}
                  >
                    <Skeleton className="h-4 w-3/4 mb-3 rounded" />
                    <Skeleton className="h-3 w-1/2 mb-2 rounded" />
                    <Skeleton className="h-3 w-1/3 rounded" />
                  </div>
                ))}
              </div>
            ) : recommendedJobs.length === 0 ? (
              <div className="relative text-center py-6">
                <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                  No recommendations right now. Complete your profile for better matches.
                </p>
                <Link
                  href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
                  className="inline-flex items-center gap-1.5 mt-2 text-sm font-medium"
                  style={{ color: 'var(--primary)' }}
                >
                  Browse all jobs
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <div className="relative flex gap-3 overflow-x-auto overflow-y-hidden pb-2 -mx-1 px-1 scrollbar-thin snap-x snap-mandatory">
                {recommendedJobs.map((job) => (
                  <Link
                    key={job.id}
                    href={`/candidate/dashboard/jobs/${job.id}`}
                    className="flex-shrink-0 w-[260px] sm:w-[280px] rounded-xl p-4 flex flex-col transition-all hover:scale-[1.02] hover:shadow-lg snap-center touch-pan-x"
                    style={{
                      background:
                        'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.7) 50%, rgba(237, 233, 254, 0.6) 100%)',
                      border: '1px solid rgba(255, 255, 255, 0.7)',
                      boxShadow: '0 4px 16px rgba(124, 58, 237, 0.08)',
                    }}
                  >
                    <div className="flex items-start gap-2 mb-2">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                        style={{
                          background:
                            'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%)',
                        }}
                      >
                        <Briefcase className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-bold truncate" style={{ color: 'var(--neutral-dark)' }}>
                          {job.title}
                        </h3>
                        <p className="text-xs truncate flex items-center gap-1 mt-0.5" style={{ color: 'var(--neutral-gray)' }}>
                          <Building2 className="w-3 h-3 flex-shrink-0" />
                          {job.employer_name ?? 'Company'}
                        </p>
                      </div>
                    </div>
                    {job.location && (
                      <p className="flex items-center gap-1.5 text-xs mt-1 truncate" style={{ color: 'var(--neutral-gray)' }}>
                        <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                        {job.location}
                      </p>
                    )}
                    {job.salary_range && (
                      <p className="flex items-center gap-1.5 text-xs mt-0.5" style={{ color: 'var(--neutral-gray)' }}>
                        <DollarSign className="w-3.5 h-3.5 flex-shrink-0" />
                        {getCurrencySymbol(job.currency)} {stripSalaryRangeCurrency(job.salary_range)}
                      </p>
                    )}
                    <p className="flex items-center gap-1.5 text-xs mt-1" style={{ color: 'var(--neutral-gray)' }}>
                      <Clock className="w-3.5 h-3.5 flex-shrink-0" />
                      {formatDate(job.created_at)}
                    </p>
                    <span className="inline-flex items-center gap-1 mt-3 text-xs font-semibold" style={{ color: 'var(--primary)' }}>
                      View details
                      <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </Link>
                ))}
              </div>
            )}
            </div>
          </div>

          {/* Profile Completion Card – soft gradient */}
          {profileCompletion < 100 && (
            <div
              className="rounded-2xl p-4 sm:p-5 mt-4 sm:mt-6"
              style={{
                background:
                  'linear-gradient(145deg, rgba(255, 251, 235, 0.9) 0%, rgba(254, 243, 199, 0.4) 50%, rgba(243, 232, 255, 0.2) 100%)',
                border: '1px solid rgba(255, 255, 255, 0.7)',
                boxShadow: '0 4px 20px rgba(0,0,0,0.04)',
              }}
            >
              <h2
                className="text-base font-semibold mb-3"
                style={{ color: 'var(--neutral-dark)' }}
              >
                Complete Your Profile
              </h2>
              {/* Progress bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span style={{ color: 'var(--neutral-gray)' }}>
                    Profile completion
                  </span>
                  <span
                    className="font-semibold"
                    style={{ color: 'var(--primary)' }}
                  >
                    {profileCompletion}%
                  </span>
                </div>
                <div
                  className="w-full h-2 rounded-full overflow-hidden"
                  style={{ background: 'var(--neutral-light)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${profileCompletion}%`,
                      background:
                        'linear-gradient(135deg, var(--primary) 0%, var(--secondary-teal) 100%)',
                    }}
                  />
                </div>
              </div>
              {/* Missing fields hints */}
              <div className="space-y-2">
                {!candidate?.email && (
                  <MissingFieldHint label="Add your email address" />
                )}
                {!candidate?.current_location && (
                  <MissingFieldHint label="Set your current location" />
                )}
                {!candidate?.date_of_birth && (
                  <MissingFieldHint label="Add date of birth" />
                )}
                {!candidate?.about && (
                  <MissingFieldHint label="Write about yourself" />
                )}
                {(!candidate?.languages_known ||
                  candidate.languages_known.length === 0) && (
                  <MissingFieldHint label="Add languages you know" />
                )}
              </div>
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_PROFILE}
                className="inline-flex items-center gap-1.5 mt-4 text-sm font-medium transition-colors hover:opacity-80"
                style={{ color: 'var(--primary)' }}
              >
                Complete Profile
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** Small helper component for missing field hints */
function MissingFieldHint({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--neutral-gray)' }}>
      <Clock className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--status-draft)' }} />
      {label}
    </div>
  );
}
