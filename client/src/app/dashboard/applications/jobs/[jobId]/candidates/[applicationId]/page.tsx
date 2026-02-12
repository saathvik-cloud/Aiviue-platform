'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ROUTES, PRIMARY_GRADIENT } from '@/constants';
import { useApplicationDetail } from '@/lib/hooks';
import { formatDate } from '@/lib/utils';
import { LoadingContent } from '@/components/ui/loading-content';
import {
  ArrowLeft,
  Download,
  FileText,
  Mail,
  MapPin,
  Phone,
  User,
} from 'lucide-react';

const RESUME_CARD_STYLE = {
  background:
    'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.9) 50%, rgba(237, 233, 254, 0.85) 100%)',
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.7)',
  boxShadow:
    '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
} as const;
const BULLET_COLOR = '#7C3AED';
const TEXT_DARK = '#374151';
const TEXT_MUTED = '#6B7280';

function ResumeValue({ value }: { value: unknown }) {
  if (value == null || value === '') return null;
  if (Array.isArray(value)) {
    return (
      <ul className="space-y-2 list-none pl-0">
        {value.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5">
            <span
              className="w-1.5 h-1.5 rounded-full mt-2 shrink-0"
              style={{ backgroundColor: BULLET_COLOR }}
            />
            <span
              className="text-sm font-medium leading-relaxed"
              style={{ color: TEXT_DARK }}
            >
              {typeof item === 'object' && item !== null ? (
                <ResumeValue value={item} />
              ) : (
                String(item)
              )}
            </span>
          </li>
        ))}
      </ul>
    );
  }
  if (typeof value === 'object') {
    return (
      <div
        className="pl-3 sm:pl-4 border-l-2 space-y-2"
        style={{ borderColor: 'rgba(124, 58, 237, 0.25)' }}
      >
        {Object.entries(value).map(([k, v]) => (
          <div key={k}>
            <span
              className="text-xs font-semibold uppercase tracking-wide capitalize"
              style={{ color: TEXT_MUTED }}
            >
              {k.replace(/_/g, ' ')}:
            </span>{' '}
            <span className="text-sm font-medium" style={{ color: TEXT_DARK }}>
              <ResumeValue value={v} />
            </span>
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

function renderResumeSections(data: Record<string, unknown> | null) {
  if (!data) return null;
  const meta = (data.meta as Record<string, unknown>) || {};
  const sections = (data.sections as Record<string, unknown>) || {};
  const hasContent =
    Object.keys(meta).length > 0 || Object.keys(sections).length > 0;
  if (!hasContent) return null;

  return (
    <div className="relative space-y-6 sm:space-y-8">
      {Object.keys(sections).length > 0 && (
        <div className="space-y-6 sm:space-y-8">
          {Object.entries(sections).map(([sectionKey, sectionValue]) => (
            <section key={sectionKey}>
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <div
                  className="w-2 h-6 rounded-full shrink-0"
                  style={{ background: PRIMARY_GRADIENT }}
                />
                <h2
                  className="text-base sm:text-lg font-bold capitalize"
                  style={{ color: TEXT_DARK }}
                >
                  {sectionKey.replace(/_/g, ' ')}
                </h2>
              </div>
              <div className="ml-1">
                <ResumeValue value={sectionValue} />
              </div>
            </section>
          ))}
        </div>
      )}
      {Object.keys(meta).length > 0 && (
        <section
          className="pt-4 sm:pt-6 border-t"
          style={{ borderColor: 'rgba(124, 58, 237, 0.2)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-2 h-5 rounded-full shrink-0"
              style={{ background: PRIMARY_GRADIENT }}
            />
            <h2
              className="text-xs font-semibold uppercase tracking-wide"
              style={{ color: TEXT_MUTED }}
            >
              Meta
            </h2>
          </div>
          <div
            className="text-xs space-y-1.5 font-medium"
            style={{ color: TEXT_MUTED }}
          >
            {Object.entries(meta).map(([k, v]) => (
              <div key={k}>
                <span className="capitalize">{k.replace(/_/g, ' ')}:</span>{' '}
                <ResumeValue value={v} />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/**
 * Application Management - Page 3: Candidate profile + resume card + download
 */
export default function ApplicationCandidateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  const applicationId = params.applicationId as string;

  const { data: application, isLoading, isError } = useApplicationDetail(
    jobId,
    applicationId
  );

  if (!isLoading && (isError || !application)) {
    router.replace(ROUTES.APPLICATIONS_JOB(jobId));
    return null;
  }

  const candidate = application?.candidate;
  const resume = application?.resume;
  const resumePdfUrl = application?.resume_pdf_url;
  const resumeSnapshot = application?.resume_snapshot;

  // Resolve resume data: platform resume.resume_data, or screening resume_snapshot
  const resumeData =
    (resume?.resume_data as Record<string, unknown>) || resumeSnapshot || null;
  const pdfUrl = resume?.pdf_url || resumePdfUrl;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={ROUTES.APPLICATIONS_JOB(jobId)}
        className="inline-flex items-center gap-2 text-sm font-medium transition-colors hover:opacity-80"
        style={{ color: 'var(--primary)' }}
      >
        <ArrowLeft className="w-4 h-4" />
        Back to applicants
      </Link>

      <LoadingContent
        isLoading={isLoading}
        isEmpty={false}
        skeletonCount={1}
        renderSkeleton={
          <div className="space-y-6">
            <div className="glass-card rounded-2xl p-6 animate-pulse">
              <div className="h-8 rounded w-1/3 mb-4 bg-white/60" />
              <div className="h-4 rounded w-1/2 bg-white/50" />
            </div>
            <div
              className="rounded-2xl p-6 animate-pulse"
              style={RESUME_CARD_STYLE}
            >
              <div className="h-6 rounded w-full mb-4" style={{ background: 'rgba(124, 58, 237, 0.1)' }} />
              <div className="h-4 rounded w-3/4 mb-2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
              <div className="h-4 rounded w-1/2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
            </div>
          </div>
        }
      >
        {/* Candidate profile card */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0"
              style={{
                background:
                  'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.12) 100%)',
              }}
            >
              {candidate?.profile_photo_url ? (
                <img
                  src={candidate.profile_photo_url}
                  alt={candidate.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <User className="w-8 h-8" style={{ color: 'var(--primary)' }} />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h1
                className="text-xl font-bold truncate"
                style={{ color: 'var(--neutral-dark)' }}
              >
                {candidate?.name ?? 'Candidate'}
              </h1>
              <p
                className="text-sm mt-1"
                style={{ color: 'var(--neutral-gray)' }}
              >
                Applied {application ? formatDate(application.applied_at) : ''}
              </p>
              <div className="flex flex-wrap gap-4 mt-4 text-sm">
                {candidate?.mobile && (
                  <span
                    className="flex items-center gap-2"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    <Phone className="w-4 h-4" />
                    {candidate.mobile}
                  </span>
                )}
                {candidate?.email && (
                  <span
                    className="flex items-center gap-2"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    <Mail className="w-4 h-4" />
                    {candidate.email}
                  </span>
                )}
                {candidate?.current_location && (
                  <span
                    className="flex items-center gap-2"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    <MapPin className="w-4 h-4" />
                    {candidate.current_location}
                  </span>
                )}
              </div>
              {candidate?.about && (
                <p
                  className="mt-4 text-sm leading-relaxed"
                  style={{ color: 'var(--neutral-gray)' }}
                >
                  {candidate.about}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Resume card + download */}
        <div
          className="rounded-2xl p-5 sm:p-6 lg:p-8 relative overflow-hidden"
          style={RESUME_CARD_STYLE}
        >
          <div
            className="absolute top-0 right-0 w-32 sm:w-40 h-32 sm:h-40 opacity-20 blur-3xl pointer-events-none"
            style={{
              background:
                'radial-gradient(circle, rgba(124, 58, 237, 0.35) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute bottom-0 left-0 w-24 sm:w-28 h-24 sm:h-28 opacity-15 blur-2xl pointer-events-none"
            style={{
              background:
                'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)',
            }}
          />

          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <h2
              className="text-lg font-bold"
              style={{ color: 'var(--neutral-dark)' }}
            >
              Resume
            </h2>
            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
              >
                <Download className="w-4 h-4" />
                Download PDF
              </a>
            )}
          </div>

          {!resumeData ||
          (Object.keys((resumeData as Record<string, unknown>).sections || {}).length === 0 &&
            Object.keys((resumeData as Record<string, unknown>).meta || {}).length === 0) ? (
            <div className="relative flex flex-col items-center justify-center py-12 sm:py-16 text-center">
              <FileText
                className="w-12 h-12 mb-3"
                style={{ color: BULLET_COLOR }}
              />
              <p className="text-sm font-medium" style={{ color: TEXT_MUTED }}>
                No structured resume content available.
              </p>
              {pdfUrl && (
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
                >
                  <Download className="w-4 h-4" /> Open PDF
                </a>
              )}
            </div>
          ) : (
            <div className="relative">
              {renderResumeSections(resumeData as Record<string, unknown>)}
            </div>
          )}
        </div>
      </LoadingContent>
    </div>
  );
}
