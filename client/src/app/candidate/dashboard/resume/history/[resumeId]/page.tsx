'use client';

import { useParams } from 'next/navigation';
import { useCandidateResumeById } from '@/lib/hooks';
import { useCandidateAuthStore } from '@/stores';
import { ROUTES } from '@/constants';
import { ArrowLeft, Download, FileText } from 'lucide-react';
import Link from 'next/link';

const RESUME_CARD_STYLE = {
  background: 'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.9) 50%, rgba(237, 233, 254, 0.85) 100%)',
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.7)',
  boxShadow: '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
} as const;

const ACCENT_GRADIENT = 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)';
const BULLET_COLOR = '#7C3AED';
const TEXT_DARK = '#374151';
const TEXT_MUTED = '#6B7280';

/**
 * Renders a value (string, number, array, or nested object) for resume display.
 * Styled with gradient accent bullets and bold/colored text to match employer cards.
 */
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
            <span className="text-sm font-medium leading-relaxed" style={{ color: TEXT_DARK }}>
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

/**
 * Single resume view – full content + download.
 */
export default function ResumeViewPage() {
  const params = useParams();
  const resumeId = params?.resumeId as string;
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const { data: resume, isLoading, isError } = useCandidateResumeById(candidate?.id, resumeId);

  if (isLoading) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4 pb-8 pt-2">
        <div className="h-10 rounded w-48 animate-pulse" style={{ background: 'var(--neutral-light)' }} />
        <div
          className="rounded-2xl p-5 sm:p-6 lg:p-8 space-y-4"
          style={RESUME_CARD_STYLE}
        >
          <div className="h-6 rounded w-full" style={{ background: 'rgba(124, 58, 237, 0.1)' }} />
          <div className="h-4 rounded w-3/4" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
          <div className="h-4 rounded w-1/2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
        </div>
      </div>
    );
  }

  if (isError || !resume) {
    return (
      <div className="w-full max-w-3xl mx-auto px-4 sm:px-6 py-12 text-center">
        <p className="text-sm font-medium mb-4" style={{ color: TEXT_MUTED }}>
          Resume not found or you don’t have access to it.
        </p>
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_RESUME_HISTORY}
          className="inline-flex items-center gap-2 text-sm font-semibold gradient-text hover:opacity-90"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Resume History
        </Link>
      </div>
    );
  }

  const data = resume.resume_data as Record<string, unknown> | undefined;
  const meta = (data?.meta as Record<string, unknown>) || {};
  const sections = (data?.sections as Record<string, unknown>) || {};

  return (
    <div className="w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4 sm:space-y-6 pb-8 pt-2">
      {/* Top bar: back link + version + download */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_RESUME_HISTORY}
          className="inline-flex items-center gap-2 text-sm font-semibold gradient-text hover:opacity-90 transition-opacity"
        >
          <ArrowLeft className="w-4 h-4 shrink-0" /> Back to Resume History
        </Link>
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <span className="text-xs font-medium" style={{ color: TEXT_MUTED }}>
            v{resume.version_number} · {resume.source === 'pdf_upload' ? 'Uploaded PDF' : 'Built with AIVI'}
          </span>
          {resume.pdf_url && (
            <a
              href={resume.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
            >
              <Download className="w-4 h-4" />
              Download PDF
            </a>
          )}
        </div>
      </div>

      {/* Resume preview card – gradient background + glass effect */}
      <div
        className="rounded-2xl p-5 sm:p-6 lg:p-8 relative overflow-hidden"
        style={RESUME_CARD_STYLE}
      >
        {/* Decorative gradient orbs (like employer job card) */}
        <div
          className="absolute top-0 right-0 w-32 sm:w-40 h-32 sm:h-40 opacity-20 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(124, 58, 237, 0.35) 0%, transparent 70%)' }}
        />
        <div
          className="absolute bottom-0 left-0 w-24 sm:w-28 h-24 sm:h-28 opacity-15 blur-2xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)' }}
        />

        {!data || (Object.keys(meta).length === 0 && Object.keys(sections).length === 0) ? (
          <div className="relative flex flex-col items-center justify-center py-12 sm:py-16 text-center">
            <FileText className="w-12 h-12 mb-3" style={{ color: BULLET_COLOR }} />
            <p className="text-sm font-medium" style={{ color: TEXT_MUTED }}>
              No structured content for this resume.
            </p>
            {resume.pdf_url && (
              <a
                href={resume.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
              >
                <Download className="w-4 h-4" /> Open PDF
              </a>
            )}
          </div>
        ) : (
          <div className="relative space-y-6 sm:space-y-8">
            {Object.keys(sections).length > 0 && (
              <div className="space-y-6 sm:space-y-8">
                {Object.entries(sections).map(([sectionKey, sectionValue]) => (
                  <section key={sectionKey}>
                    <div className="flex items-center gap-2 mb-3 sm:mb-4">
                      <div
                        className="w-2 h-6 rounded-full shrink-0"
                        style={{ background: ACCENT_GRADIENT }}
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
                    style={{ background: ACCENT_GRADIENT }}
                  />
                  <h2 className="text-xs font-semibold uppercase tracking-wide" style={{ color: TEXT_MUTED }}>
                    Meta
                  </h2>
                </div>
                <div className="text-xs space-y-1.5 font-medium" style={{ color: TEXT_MUTED }}>
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
        )}
      </div>
    </div>
  );
}
