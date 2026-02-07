'use client';

import { useCandidateResumes } from '@/lib/hooks';
import { useCandidateAuthStore } from '@/stores';
import { formatDate } from '@/lib/utils';
import { ROUTES } from '@/constants';
import { Download, FileText, History, Eye } from 'lucide-react';
import Link from 'next/link';

/**
 * Resume History – list of all past resumes with Preview and Download.
 */
export default function ResumeHistoryPage() {
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const { data: resumes, isLoading } = useCandidateResumes(candidate?.id);

  return (
    <div className="max-w-2xl mx-auto space-y-6 pb-8">
      <div className="rounded-2xl p-5 border border-[var(--neutral-border)] bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-2">
          <History className="w-5 h-5" style={{ color: 'var(--neutral-gray)' }} />
          <h1 className="text-xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
            Resume History
          </h1>
        </div>
        <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
          All your past resumes. Preview or download any version.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-center gap-4 p-4 rounded-xl border animate-pulse"
              style={{ borderColor: 'var(--neutral-border)', background: 'rgba(255,255,255,0.5)' }}
            >
              <div
                className="w-12 h-12 rounded-xl flex-shrink-0"
                style={{ background: 'var(--neutral-light)' }}
              />
              <div className="flex-1">
                <div className="h-4 rounded w-1/3 mb-2" style={{ background: 'var(--neutral-light)' }} />
                <div className="h-3 rounded w-1/2" style={{ background: 'var(--neutral-light)' }} />
              </div>
            </div>
          ))}
        </div>
      ) : resumes && resumes.length > 0 ? (
        <ul className="space-y-3">
          {resumes.map((resume) => (
            <li
              key={resume.id}
              className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 rounded-xl border"
              style={{ borderColor: 'var(--neutral-border)', background: 'rgba(255,255,255,0.5)' }}
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{
                  background:
                    resume.status === 'completed' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                }}
              >
                <FileText
                  className="w-6 h-6"
                  style={{
                    color:
                      resume.status === 'completed' ? 'var(--status-published)' : 'var(--status-draft)',
                  }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                  Resume v{resume.version_number}
                </p>
                <p className="text-xs mt-0.5" style={{ color: 'var(--neutral-gray)' }}>
                  {resume.source === 'pdf_upload' ? 'Uploaded PDF' : 'Built with AIVI'} · Created{' '}
                  {formatDate(resume.created_at)}
                  {resume.updated_at !== resume.created_at &&
                    ` · Updated ${formatDate(resume.updated_at)}`}
                </p>
                <span
                  className="inline-block mt-2 text-xs font-medium px-2 py-0.5 rounded"
                  style={{
                    background:
                      resume.status === 'completed'
                        ? 'rgba(34, 197, 94, 0.15)'
                        : 'rgba(245, 158, 11, 0.15)',
                    color:
                      resume.status === 'completed' ? 'var(--status-published)' : 'var(--status-draft)',
                  }}
                >
                  {resume.status === 'completed' ? 'Completed' : 'In progress'}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <Link
                  href={ROUTES.CANDIDATE_DASHBOARD_RESUME_VIEW(resume.id)}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-colors hover:opacity-90"
                  style={{ background: 'var(--primary-50)', color: 'var(--primary)' }}
                >
                  <Eye className="w-4 h-4" />
                  Preview
                </Link>
                {resume.pdf_url && (
                  <a
                    href={resume.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-colors hover:opacity-90"
                    style={{ background: 'var(--neutral-light)', color: 'var(--neutral-dark)' }}
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-center py-12 rounded-2xl border" style={{ borderColor: 'var(--neutral-border)' }}>
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-3"
            style={{ background: 'rgba(124, 58, 237, 0.1)' }}
          >
            <FileText className="w-7 h-7" style={{ color: 'var(--primary)' }} />
          </div>
          <p className="text-sm font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
            No resumes yet
          </p>
          <p className="text-xs mb-4" style={{ color: 'var(--neutral-gray)' }}>
            Build or upload a resume from the Resume page to see it here.
          </p>
          <Link
            href={ROUTES.CANDIDATE_DASHBOARD_RESUME}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium"
            style={{ background: 'var(--primary)', color: 'white' }}
          >
            Go to Resume
          </Link>
        </div>
      )}
    </div>
  );
}
