'use client';

import Link from 'next/link';
import { ROUTES } from '@/constants';
import {
  EMPLOYER_GLASS_CARD,
  EMPLOYER_QUICK_ACTION_CARD_STYLES,
  EMPLOYER_RECENT_JOB_ROW_STYLES,
  EMPLOYER_STAT_CARD_GRADIENTS,
} from '@/constants/ui';
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
  Clock,
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
    },
    {
      label: 'Published',
      value: stats?.published ?? 0,
      icon: CheckCircle,
      trend: '+8%',
      trendUp: true,
    },
    {
      label: 'Drafts',
      value: stats?.draft ?? 0,
      icon: FileText,
      trend: '3 pending',
      trendUp: null,
    },
    {
      label: 'Closed',
      value: stats?.closed ?? 0,
      icon: XCircle,
      trend: '-5%',
      trendUp: false,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
          Welcome back, {employer?.name?.split(' ')[0] || 'there'}! 👋
        </h1>
        <p className="text-sm sm:text-base mt-1" style={{ color: 'var(--neutral-gray)' }}>
          Here&apos;s what&apos;s happening with your job postings
        </p>
      </div>

      {/* Stats Cards - glassmorphic + light gradients from constants */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          const cardStyle = EMPLOYER_STAT_CARD_GRADIENTS[index];
          return (
            <div
              key={stat.label}
              className="rounded-2xl p-5 relative overflow-hidden transition-all duration-300 hover:translate-y-[-3px]"
              style={{
                background: cardStyle.cardBg,
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                border: cardStyle.border,
                boxShadow: cardStyle.shadow,
              }}
            >
              <div
                className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-20 blur-2xl transform translate-x-8 -translate-y-8"
                style={{ background: cardStyle.gradient }}
              />
              <div className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center"
                    style={{ background: cardStyle.bgLight }}
                  >
                    <Icon className="w-5 h-5" style={{ color: cardStyle.iconColor }} />
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
          <div
            className="rounded-2xl p-5 h-full transition-all duration-300 hover:shadow-[0_8px_32px_rgba(124,58,237,0.12)]"
            style={EMPLOYER_GLASS_CARD}
          >
            <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--neutral-dark)' }}>
              Quick Actions
            </h2>
            <div className="space-y-3">
              {[
                { href: ROUTES.JOB_NEW, icon: Plus, title: 'Post a New Job', subtitle: 'Use AIVI to extract details', index: 0 },
                { href: ROUTES.JOBS, icon: Briefcase, title: 'View All Jobs', subtitle: 'Manage your postings', index: 1 },
                { href: ROUTES.DASHBOARD_PROFILE, icon: TrendingUp, title: 'Update Profile', subtitle: 'Company details', index: 2 },
              ].map(({ href, icon: Icon, title, subtitle, index }) => {
                const style = EMPLOYER_QUICK_ACTION_CARD_STYLES[index];
                return (
                  <Link
                    key={href}
                    href={href}
                    className="flex items-center gap-3 p-3 rounded-xl transition-all duration-300 hover:scale-[1.02]"
                    style={{
                      background: style.cardBg,
                      backdropFilter: 'blur(12px)',
                      WebkitBackdropFilter: 'blur(12px)',
                      border: style.border,
                      boxShadow: style.shadow,
                    }}
                  >
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                      style={{ background: style.iconBg }}
                    >
                      <Icon className="w-5 h-5" style={{ color: style.iconColor }} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                        {title}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                        {subtitle}
                      </p>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="lg:col-span-2">
          <div
            className="rounded-2xl p-5 transition-all duration-300 hover:shadow-[0_8px_32px_rgba(124,58,237,0.12)]"
            style={EMPLOYER_GLASS_CARD}
          >
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
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="animate-pulse flex items-center gap-4 p-4 rounded-xl"
                    style={{
                      background: 'linear-gradient(145deg, rgba(250, 245, 255, 0.85) 0%, rgba(243, 232, 255, 0.75) 100%)',
                      border: '1px solid rgba(255, 255, 255, 0.6)',
                    }}
                  >
                    <div className="w-12 h-12 rounded-xl bg-white/60" />
                    <div className="flex-1">
                      <div className="h-4 rounded w-1/2 mb-2 bg-white/50" />
                      <div className="h-3 rounded w-1/3 bg-white/40" />
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
                {recentJobs?.items.map((job) => {
                  const rowStyle = EMPLOYER_RECENT_JOB_ROW_STYLES[job.status] ?? EMPLOYER_RECENT_JOB_ROW_STYLES.default;
                  const iconBg =
                    job.status === 'published'
                      ? 'linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(74, 222, 128, 0.15) 100%)'
                      : job.status === 'draft'
                        ? 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(251, 191, 36, 0.15) 100%)'
                        : 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%)';
                  const iconColor =
                    job.status === 'published' ? 'var(--status-published)' : job.status === 'draft' ? 'var(--status-draft)' : 'var(--status-closed)';
                  return (
                    <Link
                      key={job.id}
                      href={ROUTES.JOB_DETAILS(job.id)}
                      className="flex items-center gap-4 p-4 rounded-xl transition-all duration-300 hover:scale-[1.01]"
                      style={{
                        background: rowStyle.cardBg,
                        backdropFilter: 'blur(12px)',
                        WebkitBackdropFilter: 'blur(12px)',
                        border: rowStyle.border,
                        boxShadow: rowStyle.shadow,
                      }}
                    >
                      <div
                        className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                        style={{ background: iconBg }}
                      >
                        <Briefcase className="w-5 h-5" style={{ color: iconColor }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate" style={{ color: 'var(--neutral-dark)' }}>
                          {job.title}
                        </p>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs" style={{ color: 'var(--neutral-gray)' }}>
                          {job.location && (
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3 h-3 flex-shrink-0" />
                              <span className="truncate">{job.location}</span>
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 flex-shrink-0" />
                            {formatDate(job.created_at)}
                          </span>
                        </div>
                      </div>
                      <span className={`status-badge status-${job.status} text-xs flex-shrink-0`}>
                        {capitalize(job.status)}
                      </span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
