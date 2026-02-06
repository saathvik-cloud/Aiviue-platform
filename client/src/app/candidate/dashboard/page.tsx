'use client';

import { ROUTES } from '@/constants';
import { useCandidateAuthStore } from '@/stores';
import {
    ArrowRight,
    Briefcase,
    CheckCircle,
    Clock,
    FileText,
    Sparkles,
    User
} from 'lucide-react';
import Link from 'next/link';

/**
 * Candidate Dashboard Home Page
 *
 * Shows welcome message, profile completion status, quick actions,
 * and a placeholder for job recommendations (Step 3.8).
 */
export default function CandidateDashboardPage() {
  const candidate = useCandidateAuthStore((state) => state.candidate);

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

  const statCards = [
    {
      label: 'Profile',
      value: `${profileCompletion}%`,
      sublabel: profileCompletion === 100 ? 'Complete' : 'Incomplete',
      icon: User,
      gradient: 'linear-gradient(135deg, #14B8A6 0%, #5EEAD4 100%)',
      bgLight: 'rgba(20, 184, 166, 0.1)',
      iconColor: 'var(--secondary-teal)',
    },
    {
      label: 'Resume',
      value: candidate?.profile_status === 'complete' ? '1' : '0',
      sublabel: 'Active resume',
      icon: FileText,
      gradient: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
      bgLight: 'rgba(124, 58, 237, 0.1)',
      iconColor: 'var(--primary)',
    },
    {
      label: 'Job Matches',
      value: '--',
      sublabel: 'Coming soon',
      icon: Briefcase,
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)',
      bgLight: 'rgba(245, 158, 11, 0.1)',
      iconColor: '#F59E0B',
    },
    {
      label: 'Applications',
      value: '0',
      sublabel: 'Applied jobs',
      icon: CheckCircle,
      gradient: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)',
      bgLight: 'rgba(34, 197, 94, 0.1)',
      iconColor: 'var(--status-published)',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1
          className="text-2xl sm:text-3xl font-bold"
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

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="stat-card rounded-2xl p-5 relative overflow-hidden">
              {/* Background decoration */}
              <div
                className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-10 blur-2xl transform translate-x-8 -translate-y-8"
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
                  className="text-3xl sm:text-4xl font-bold mb-1"
                  style={{ color: 'var(--neutral-dark)' }}
                >
                  {stat.value}
                </p>
                <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                  {stat.sublabel}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="lg:col-span-1">
          <div className="glass-card rounded-2xl p-5 h-full">
            <h2
              className="text-base font-semibold mb-4"
              style={{ color: 'var(--neutral-dark)' }}
            >
              Quick Actions
            </h2>
            <div className="space-y-3">
              {/* Build Resume */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_RESUME}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02]"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)',
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{
                    background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)',
                  }}
                >
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p
                    className="text-sm font-medium"
                    style={{ color: 'var(--neutral-dark)' }}
                  >
                    Build Resume with AIVI
                  </p>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    AI-powered resume builder
                  </p>
                </div>
              </Link>

              {/* Browse Jobs */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02] bg-white/60 hover:bg-white"
                style={{ border: '1px solid var(--neutral-border)' }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'var(--primary-50)' }}
                >
                  <Briefcase
                    className="w-5 h-5"
                    style={{ color: 'var(--primary)' }}
                  />
                </div>
                <div>
                  <p
                    className="text-sm font-medium"
                    style={{ color: 'var(--neutral-dark)' }}
                  >
                    Browse Jobs
                  </p>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    Find matching opportunities
                  </p>
                </div>
              </Link>

              {/* Update Profile */}
              <Link
                href={ROUTES.CANDIDATE_DASHBOARD_PROFILE}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02] bg-white/60 hover:bg-white"
                style={{ border: '1px solid var(--neutral-border)' }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'rgba(20, 184, 166, 0.1)' }}
                >
                  <User
                    className="w-5 h-5"
                    style={{ color: 'var(--secondary-teal)' }}
                  />
                </div>
                <div>
                  <p
                    className="text-sm font-medium"
                    style={{ color: 'var(--neutral-dark)' }}
                  >
                    Update Profile
                  </p>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    Complete your details
                  </p>
                </div>
              </Link>
            </div>
          </div>
        </div>

        {/* Job Recommendations Placeholder */}
        <div className="lg:col-span-2">
          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2
                className="text-base font-semibold"
                style={{ color: 'var(--neutral-dark)' }}
              >
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

            {/* Placeholder - will be populated in Step 3.8 */}
            <div className="text-center py-10">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{
                  background:
                    'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)',
                }}
              >
                <Briefcase
                  className="w-8 h-8"
                  style={{ color: 'var(--primary)' }}
                />
              </div>
              <p
                className="text-sm font-medium mb-1"
                style={{ color: 'var(--neutral-dark)' }}
              >
                Build your resume first
              </p>
              <p
                className="text-xs mb-4"
                style={{ color: 'var(--neutral-gray)' }}
              >
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
          </div>

          {/* Profile Completion Card */}
          {profileCompletion < 100 && (
            <div className="glass-card rounded-2xl p-5 mt-6">
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
