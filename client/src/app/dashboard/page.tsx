'use client';

import Link from 'next/link';
import { ROUTES } from '@/constants';
import { useAuthStore } from '@/stores';
import { useJobStats, useJobs } from '@/lib/hooks';
import { formatDate, capitalize } from '@/lib/utils';
import { 
  Briefcase, 
  CheckCircle, 
  FileText, 
  XCircle,
  Plus,
  ArrowRight,
  TrendingUp,
  MapPin,
  ArrowUpRight,
  Clock
} from 'lucide-react';

/**
 * Dashboard Home - Nexus-inspired design with stat cards
 */
export default function DashboardPage() {
  const employer = useAuthStore((state) => state.employer);
  
  const { data: stats, isLoading: statsLoading } = useJobStats(employer?.id);
  const { data: recentJobs, isLoading: jobsLoading } = useJobs(
    { employer_id: employer?.id },
    undefined,
    5
  );

  const statCards = [
    {
      label: 'Total Jobs',
      value: stats?.total ?? 0,
      icon: Briefcase,
      trend: '+12%',
      trendUp: true,
      gradient: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
      bgLight: 'rgba(124, 58, 237, 0.1)',
    },
    {
      label: 'Published',
      value: stats?.published ?? 0,
      icon: CheckCircle,
      trend: '+8%',
      trendUp: true,
      gradient: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)',
      bgLight: 'rgba(34, 197, 94, 0.1)',
    },
    {
      label: 'Drafts',
      value: stats?.draft ?? 0,
      icon: FileText,
      trend: '3 pending',
      trendUp: null,
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)',
      bgLight: 'rgba(245, 158, 11, 0.1)',
    },
    {
      label: 'Closed',
      value: stats?.closed ?? 0,
      icon: XCircle,
      trend: '-5%',
      trendUp: false,
      gradient: 'linear-gradient(135deg, #EC4899 0%, #F472B6 100%)',
      bgLight: 'rgba(236, 72, 153, 0.1)',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
            Welcome back, {employer?.name?.split(' ')[0] || 'there'}! 👋
          </h1>
          <p className="text-sm sm:text-base mt-1" style={{ color: 'var(--neutral-gray)' }}>
            Here&apos;s what&apos;s happening with your job postings
          </p>
        </div>
        <Link
          href={ROUTES.JOB_NEW}
          className="btn-gradient flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold"
        >
          <Plus className="w-5 h-5" />
          Post a Job
        </Link>
      </div>

      {/* Stats Cards - Nexus Style */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div 
              key={stat.label}
              className="stat-card rounded-2xl p-5 relative overflow-hidden"
            >
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
                    <Icon className="w-5 h-5" style={{ color: stat.gradient.includes('#7C3AED') ? 'var(--primary)' : stat.gradient.includes('#22C55E') ? 'var(--status-published)' : stat.gradient.includes('#F59E0B') ? 'var(--status-draft)' : 'var(--accent)' }} />
                  </div>
                  {stat.trendUp !== null && (
                    <div className={`flex items-center gap-1 text-xs font-medium ${stat.trendUp ? 'text-green-600' : 'text-red-500'}`}>
                      {stat.trend}
                      <ArrowUpRight className={`w-3 h-3 ${!stat.trendUp && 'rotate-90'}`} />
                    </div>
                  )}
                  {stat.trendUp === null && (
                    <div className="text-xs font-medium" style={{ color: 'var(--neutral-gray)' }}>
                      {stat.trend}
                    </div>
                  )}
                </div>
                <p className="text-3xl sm:text-4xl font-bold mb-1" style={{ color: 'var(--neutral-dark)' }}>
                  {statsLoading ? '-' : stat.value}
                </p>
                <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                  {stat.label}
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
            <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--neutral-dark)' }}>
              Quick Actions
            </h2>
            <div className="space-y-3">
              <Link
                href={ROUTES.JOB_NEW}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02]"
                style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
              >
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
                >
                  <Plus className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                    Post a New Job
                  </p>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    Use AIVI to extract details
                  </p>
                </div>
              </Link>

              <Link
                href={ROUTES.JOBS}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02] bg-white/60 hover:bg-white"
                style={{ border: '1px solid var(--neutral-border)' }}
              >
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'var(--primary-50)' }}
                >
                  <Briefcase className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                    View All Jobs
                  </p>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    Manage your postings
                  </p>
                </div>
              </Link>

              <Link
                href={ROUTES.DASHBOARD_PROFILE}
                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:scale-[1.02] bg-white/60 hover:bg-white"
                style={{ border: '1px solid var(--neutral-border)' }}
              >
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: 'var(--accent-50)' }}
                >
                  <TrendingUp className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                    Update Profile
                  </p>
                  <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                    Company details
                  </p>
                </div>
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="lg:col-span-2">
          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold" style={{ color: 'var(--neutral-dark)' }}>
                Recent Jobs
              </h2>
              <Link
                href={ROUTES.JOBS}
                className="text-sm font-medium flex items-center gap-1 transition-colors hover:opacity-80"
                style={{ color: 'var(--primary)' }}
              >
                View all
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {jobsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse flex items-center gap-4 p-4 rounded-xl bg-white/50">
                    <div className="w-12 h-12 bg-gray-200 rounded-xl" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                      <div className="h-3 bg-gray-200 rounded w-1/3" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recentJobs?.items.length === 0 ? (
              <div className="text-center py-10">
                <div 
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                  style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
                >
                  <Briefcase className="w-8 h-8" style={{ color: 'var(--primary)' }} />
                </div>
                <p className="text-sm font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
                  No jobs yet
                </p>
                <p className="text-xs mb-4" style={{ color: 'var(--neutral-gray)' }}>
                  Create your first job posting
                </p>
                <Link
                  href={ROUTES.JOB_NEW}
                  className="btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Post a Job
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {recentJobs?.items.map((job) => (
                  <Link
                    key={job.id}
                    href={ROUTES.JOB_DETAILS(job.id)}
                    className="flex items-center gap-4 p-4 rounded-xl transition-all hover:bg-white/80 bg-white/50"
                    style={{ border: '1px solid transparent' }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--neutral-border)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
                  >
                    <div 
                      className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                      style={{ 
                        background: job.status === 'published' 
                          ? 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(74, 222, 128, 0.1) 100%)'
                          : job.status === 'draft'
                          ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%)'
                          : 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%)'
                      }}
                    >
                      <Briefcase 
                        className="w-5 h-5" 
                        style={{ 
                          color: job.status === 'published' 
                            ? 'var(--status-published)' 
                            : job.status === 'draft'
                            ? 'var(--status-draft)'
                            : 'var(--status-closed)'
                        }} 
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: 'var(--neutral-dark)' }}>
                        {job.title}
                      </p>
                      <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--neutral-gray)' }}>
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {job.location}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(job.created_at)}
                        </span>
                      </div>
                    </div>
                    <span className={`status-badge status-${job.status} text-xs`}>
                      {capitalize(job.status)}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
