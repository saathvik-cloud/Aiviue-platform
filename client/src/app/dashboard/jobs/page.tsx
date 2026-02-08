'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ROUTES, WORK_TYPES, JOB_STATUS } from '@/constants';
import { useAuthStore } from '@/stores';
import { useJobs } from '@/lib/hooks';
import { formatDate, capitalize } from '@/lib/utils';
import { SelectDropdown } from '@/components';
import { LoadingContent } from '@/components/ui/loading-content';
import type { JobStatus, WorkType } from '@/types';
import { 
  Briefcase, 
  Plus,
  Search,
  Filter,
  MapPin,
  Calendar,
  ChevronRight,
  X,
  CheckCircle,
  FileText,
  XCircle,
  Building,
  Home,
  Wifi
} from 'lucide-react';

// Status filter options with icons
const STATUS_OPTIONS = [
  { value: '', label: 'All Status' },
  { value: JOB_STATUS.PUBLISHED, label: 'Published', icon: <CheckCircle className="w-4 h-4" style={{ color: 'var(--status-published)' }} /> },
  { value: JOB_STATUS.DRAFT, label: 'Draft', icon: <FileText className="w-4 h-4" style={{ color: 'var(--status-draft)' }} /> },
  { value: JOB_STATUS.CLOSED, label: 'Closed', icon: <XCircle className="w-4 h-4" style={{ color: 'var(--status-closed)' }} /> },
];

// Work type filter options with icons
const WORK_TYPE_OPTIONS = [
  { value: '', label: 'All Work Types' },
  { value: 'onsite', label: 'On-site', icon: <Building className="w-4 h-4" style={{ color: 'var(--primary)' }} /> },
  { value: 'remote', label: 'Remote', icon: <Wifi className="w-4 h-4" style={{ color: 'var(--secondary-teal)' }} /> },
  { value: 'hybrid', label: 'Hybrid', icon: <Home className="w-4 h-4" style={{ color: 'var(--accent)' }} /> },
];

/**
 * Jobs List Page - Glassmorphism design with custom dropdowns
 */
export default function JobsPage() {
  const employer = useAuthStore((state) => state.employer);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<JobStatus | ''>('');
  const [workTypeFilter, setWorkTypeFilter] = useState<WorkType | ''>('');
  const [showFilters, setShowFilters] = useState(false);

  const { data: jobs, isLoading } = useJobs(
    {
      employer_id: employer?.id,
      status: statusFilter || undefined,
      work_type: workTypeFilter || undefined,
      search: searchQuery || undefined,
    },
    undefined,
    50
  );

  const clearFilters = () => {
    setStatusFilter('');
    setWorkTypeFilter('');
    setSearchQuery('');
  };

  const hasFilters = statusFilter || workTypeFilter || searchQuery;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
            Jobs
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>
            {jobs?.total_count ?? 0} job{(jobs?.total_count ?? 0) !== 1 ? 's' : ''} total
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

      {/* Search & Filters */}
      <div className="glass-card rounded-2xl p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--neutral-muted)' }} />
            <input
              type="text"
              placeholder="Search jobs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/80 hover:bg-white focus:bg-white focus:ring-2"
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>

          {/* Filter Toggle (Mobile) */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="sm:hidden btn-glass flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium"
            style={{ color: 'var(--neutral-dark)' }}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasFilters && (
              <span 
                className="w-5 h-5 rounded-full text-xs flex items-center justify-center text-white"
                style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
              >
                {[statusFilter, workTypeFilter].filter(Boolean).length}
              </span>
            )}
          </button>

          {/* Filters - Using custom SelectDropdown */}
          <div className={`${showFilters ? 'flex' : 'hidden'} sm:flex flex-col sm:flex-row gap-3`}>
            <SelectDropdown
              options={STATUS_OPTIONS}
              value={statusFilter}
              onChange={(val) => setStatusFilter(val as JobStatus | '')}
              placeholder="All Status"
              className="w-full sm:w-44"
            />

            <SelectDropdown
              options={WORK_TYPE_OPTIONS}
              value={workTypeFilter}
              onChange={(val) => setWorkTypeFilter(val as WorkType | '')}
              placeholder="All Work Types"
              className="w-full sm:w-48"
            />

            {hasFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center justify-center gap-1 px-3 py-3 rounded-xl text-sm font-medium transition-colors hover:bg-red-50"
                style={{ color: 'var(--status-closed)' }}
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Jobs List */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <LoadingContent
          isLoading={isLoading}
          isEmpty={(jobs?.items.length ?? 0) === 0}
          skeletonCount={5}
          renderSkeleton={
            <div className="p-5 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="animate-pulse flex items-center gap-4 p-4 rounded-xl bg-white/50">
                  <div className="w-12 h-12 bg-gray-200 rounded-xl" />
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-1/3" />
                  </div>
                </div>
              ))}
            </div>
          }
          emptyContent={
            <div className="text-center py-16 px-4">
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
              >
                <Briefcase className="w-10 h-10" style={{ color: 'var(--primary)' }} />
              </div>
              <p className="text-lg font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
                {hasFilters ? 'No jobs match your filters' : 'No jobs yet'}
              </p>
              <p className="text-sm mb-6" style={{ color: 'var(--neutral-gray)' }}>
                {hasFilters ? 'Try adjusting your filters' : 'Create your first job posting'}
              </p>
              {hasFilters ? (
                <button
                  onClick={clearFilters}
                  className="btn-glass px-5 py-2.5 rounded-xl text-sm font-medium"
                  style={{ color: 'var(--primary)' }}
                >
                  Clear Filters
                </button>
              ) : (
                <Link
                  href={ROUTES.JOB_NEW}
                  className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Post a Job
                </Link>
              )}
            </div>
          }
        >
          <div className="divide-y" style={{ borderColor: 'rgba(226, 232, 240, 0.5)' }}>
            {jobs?.items.map((job) => (
              <Link
                key={job.id}
                href={ROUTES.JOB_DETAILS(job.id)}
                className="flex items-center gap-4 p-5 transition-all hover:bg-white/80"
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
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold truncate" style={{ color: 'var(--neutral-dark)' }}>
                        {job.title}
                      </h3>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs" style={{ color: 'var(--neutral-gray)' }}>
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" />
                            {job.location}
                          </span>
                        )}
                        {job.work_type && (
                          <span className="hidden sm:inline">
                            {WORK_TYPES.find(t => t.value === job.work_type)?.label}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" />
                          {formatDate(job.created_at)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`status-badge status-${job.status} text-xs`}>
                        {capitalize(job.status)}
                      </span>
                      <ChevronRight className="w-5 h-5 hidden sm:block" style={{ color: 'var(--neutral-muted)' }} />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </LoadingContent>
      </div>
    </div>
  );
}
