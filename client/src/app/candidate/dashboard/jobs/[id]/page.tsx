'use client';

/**
 * Candidate Job Detail Page – multiple gradient/glass tiles (employer-style).
 * Tiles: Location, Salary, Experience, Work Type, Description, Requirements, Additional info.
 */

import { ROUTES, WORK_TYPES } from '@/constants';
import { useJob } from '@/lib/hooks';
import { formatDate, formatSalaryRange, getCurrencySymbol, stripSalaryRangeCurrency } from '@/lib/utils';
import {
  ArrowLeft,
  Briefcase,
  MapPin,
  Building2,
  DollarSign,
  Clock,
  Calendar,
  CheckCircle,
  Globe,
} from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

interface DescriptionSection {
  title: string;
  color: string;
  bullets: string[];
}

function parseIntoSections(text: string | undefined | null): DescriptionSection[] {
  if (!text) return [];
  const paragraphs = text
    .split(/[\n\r]+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);
  const themes = [
    { title: 'About this role', color: '#7C3AED' },
    { title: 'Your responsibilities', color: '#2563EB' },
    { title: 'What you\'ll do', color: '#0891B2' },
    { title: 'Why join', color: '#059669' },
  ];
  if (paragraphs.length <= 1) {
    return [{ title: themes[0].title, color: themes[0].color, bullets: paragraphs }];
  }
  const sections: DescriptionSection[] = [];
  const itemsPerSection = Math.ceil(paragraphs.length / themes.length);
  for (let i = 0; i < themes.length && i * itemsPerSection < paragraphs.length; i++) {
    const start = i * itemsPerSection;
    const end = Math.min(start + itemsPerSection, paragraphs.length);
    let sectionBullets = paragraphs.slice(start, end);
    const splitBullets: string[] = [];
    sectionBullets.forEach((para) => {
      if (para.length > 200) {
        const sentences = para.match(/[^.!?]+[.!?]+/g) || [para];
        splitBullets.push(...sentences.map((s) => s.trim()).filter((s) => s.length > 10));
      } else {
        splitBullets.push(para);
      }
    });
    sections.push({
      title: themes[i].title,
      color: themes[i].color,
      bullets: splitBullets.slice(0, 4),
    });
  }
  return sections;
}

function parseIntoBullets(text: string | undefined | null): string[] {
  if (!text) return [];
  return text
    .split(/[\n\r]+/)
    .map((line) => line.replace(/^[-•*\d.)\s]+/, '').trim())
    .filter((line) => line.length > 0);
}

export default function CandidateJobDetailPage() {
  const params = useParams();
  const jobId = typeof params.id === 'string' ? params.id : undefined;
  const { data: job, isLoading, error } = useJob(jobId);

  if (isLoading) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 space-y-4 pb-8">
        <div className="h-10 rounded w-48 animate-pulse" style={{ background: 'var(--neutral-light)' }} />
        <div className="rounded-2xl p-6 animate-pulse space-y-4" style={{ background: 'rgba(124, 58, 237, 0.06)' }}>
          <div className="h-6 rounded w-3/4" style={{ background: 'var(--neutral-light)' }} />
          <div className="h-4 rounded w-1/2" style={{ background: 'var(--neutral-light)' }} />
          <div className="h-20 rounded w-full" style={{ background: 'var(--neutral-light)' }} />
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-12 text-center">
        <p className="text-sm font-medium mb-4" style={{ color: 'var(--neutral-gray)' }}>
          Job not found or no longer available.
        </p>
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
          className="inline-flex items-center gap-2 text-sm font-semibold gradient-text"
        >
          <ArrowLeft className="w-4 h-4" /> Back to jobs
        </Link>
      </div>
    );
  }

  const descriptionSections = parseIntoSections(job.description);
  const requirementsBullets = parseIntoBullets(job.requirements);
  const workTypeLabel =
    job.work_type && WORK_TYPES.find((t) => t.value === job.work_type)
      ? WORK_TYPES.find((t) => t.value === job.work_type)!.label
      : job.work_type?.replace('_', '-') ?? 'Not specified';
  const locationStr =
    [job.city, job.state, job.country].filter(Boolean).join(', ') || job.location || 'Not specified';
  const currency = job.currency || undefined;
  const salaryStr =
    job.salary_range
      ? `${getCurrencySymbol(currency)} ${stripSalaryRangeCurrency(job.salary_range)}`
      : formatSalaryRange(job.salary_range_min, job.salary_range_max, currency) ||
        'Not specified';
  const experienceStr =
    job.experience_range ||
    (job.experience_min != null || job.experience_max != null
      ? `${job.experience_min ?? 0}-${job.experience_max ?? 0} years`
      : 'Not specified');

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 space-y-4 sm:space-y-6 pb-8">
      <Link
        href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
        className="inline-flex items-center gap-2 text-sm font-semibold gradient-text hover:opacity-90"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to jobs
      </Link>

      {/* Hero: title + company */}
      <div
        className="rounded-2xl p-5 sm:p-6 relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(236, 72, 153, 0.06) 100%)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.6)',
          boxShadow: '0 8px 32px rgba(124, 58, 237, 0.08)',
        }}
      >
        <div className="flex items-start gap-4">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(236, 72, 153, 0.15) 100%)',
            }}
          >
            <Briefcase className="w-7 h-7" style={{ color: 'var(--primary)' }} />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl sm:text-2xl font-bold" style={{ color: '#374151' }}>
              {job.title}
            </h1>
            <p className="text-sm font-semibold mt-1 flex items-center gap-1" style={{ color: '#6B7280' }}>
              <Building2 className="w-4 h-4" style={{ color: 'var(--primary)' }} />
              {job.employer_name ?? 'Company'}
            </p>
          </div>
        </div>
      </div>

      {/* 4 info tiles: Location, Salary, Experience, Work Type */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <Tile
          icon={<MapPin className="w-5 h-5" style={{ color: '#7C3AED' }} />}
          label="Location"
          value={locationStr}
          labelColor="#7C3AED"
          style={{
            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%)',
            border: '1px solid rgba(124, 58, 237, 0.15)',
          }}
          iconBg="linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)"
        />
        <Tile
          icon={<DollarSign className="w-5 h-5" style={{ color: '#22C55E' }} />}
          label="Salary"
          value={salaryStr}
          labelColor="#22C55E"
          style={{
            background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(74, 222, 128, 0.08) 100%)',
            border: '1px solid rgba(34, 197, 94, 0.15)',
          }}
          iconBg="linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(74, 222, 128, 0.2) 100%)"
        />
        <Tile
          icon={<Briefcase className="w-5 h-5" style={{ color: '#F97316' }} />}
          label="Experience"
          value={experienceStr}
          labelColor="#F97316"
          style={{
            background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(251, 146, 60, 0.08) 100%)',
            border: '1px solid rgba(249, 115, 22, 0.15)',
          }}
          iconBg="linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(251, 146, 60, 0.2) 100%)"
        />
        <Tile
          icon={<Globe className="w-5 h-5" style={{ color: '#EC4899' }} />}
          label="Work Type"
          value={workTypeLabel}
          labelColor="#EC4899"
          style={{
            background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(244, 114, 182, 0.08) 100%)',
            border: '1px solid rgba(236, 72, 153, 0.15)',
          }}
          iconBg="linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(244, 114, 182, 0.2) 100%)"
        />
      </div>

      {/* Description card */}
      <div
        className="rounded-2xl p-5 sm:p-6 relative overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(245, 243, 240, 0.95) 0%, rgba(231, 225, 217, 0.85) 50%, rgba(214, 205, 193, 0.75) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.6)',
          boxShadow: '0 8px 32px rgba(120, 100, 80, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
        }}
      >
        <div className="absolute top-0 right-0 w-40 h-40 opacity-20 blur-3xl pointer-events-none" style={{ background: 'radial-gradient(circle, rgba(180, 160, 140, 0.3) 0%, transparent 70%)' }} />
        <div className="flex items-center gap-2 mb-4 sm:mb-5 relative">
          <div className="w-2 h-6 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }} />
          <h2 className="text-base font-bold" style={{ color: '#374151' }}>Description</h2>
        </div>
        <div className="space-y-5 relative">
          {descriptionSections.length > 0 ? (
            descriptionSections.map((section, i) => (
              <div key={i}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: section.color }}>{section.title}</h3>
                <div className="space-y-2 ml-1">
                  {section.bullets.map((bullet, j) => (
                    <div key={j} className="flex items-start gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ backgroundColor: section.color }} />
                      <span className="text-sm leading-relaxed" style={{ color: '#4A4A4A' }}>{bullet}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : job.description ? (
            <p className="text-sm whitespace-pre-wrap" style={{ color: '#4A4A4A' }}>{job.description}</p>
          ) : (
            <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>No description provided.</p>
          )}
        </div>
      </div>

      {/* Requirements card */}
      <div
        className="rounded-2xl p-5 sm:p-6 relative overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(240, 245, 243, 0.95) 0%, rgba(220, 235, 230, 0.85) 50%, rgba(195, 220, 210, 0.75) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(20, 184, 166, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
        }}
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-6 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #2DD4BF 100%)' }} />
          <h2 className="text-base font-bold" style={{ color: '#374151' }}>Requirements</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2.5 text-sm leading-relaxed">
          {requirementsBullets.length > 0 ? (
            requirementsBullets.map((bullet, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#14B8A6' }} />
                <span style={{ color: '#4A4A4A' }}>{bullet}</span>
              </div>
            ))
          ) : (
            <p style={{ color: 'var(--neutral-gray)' }}>No requirements specified.</p>
          )}
        </div>
      </div>

      {/* Additional info: posted date + openings */}
      <div
        className="rounded-2xl p-5 relative overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(245, 243, 250, 0.95) 0%, rgba(235, 230, 245, 0.85) 50%, rgba(220, 215, 235, 0.75) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(99, 102, 241, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
        }}
      >
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-5 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, #6366F1 0%, #818CF8 100%)' }} />
          <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#6B7280' }}>Additional information</h2>
        </div>
        <div className="flex flex-wrap gap-4 sm:gap-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(99, 102, 241, 0.1)' }}>
              <Calendar className="w-4 h-4" style={{ color: '#6366F1' }} />
            </div>
            <div>
              <p className="text-xs font-medium" style={{ color: '#6B7280' }}>Posted</p>
              <p className="text-sm font-semibold" style={{ color: '#374151' }}>{formatDate(job.created_at)}</p>
            </div>
          </div>
          {job.openings_count > 0 && (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'rgba(34, 197, 94, 0.1)' }}>
                <Briefcase className="w-4 h-4" style={{ color: '#22C55E' }} />
              </div>
              <div>
                <p className="text-xs font-medium" style={{ color: '#6B7280' }}>Positions</p>
                <p className="text-sm font-semibold" style={{ color: '#374151' }}>
                  {job.openings_count} position{job.openings_count !== 1 ? 's' : ''} open
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Tile({
  icon,
  label,
  value,
  labelColor,
  style,
  iconBg,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  labelColor: string;
  style: React.CSSProperties;
  iconBg: string;
}) {
  return (
    <div
      className="rounded-xl p-4 relative overflow-hidden transition-all hover:scale-[1.02]"
      style={{ ...style, backdropFilter: 'blur(10px)' }}
    >
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: iconBg }}
        >
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: labelColor }}>{label}</p>
          <p className="text-sm font-semibold truncate mt-0.5" style={{ color: '#374151' }}>{value}</p>
        </div>
      </div>
    </div>
  );
}
