'use client';

import { ROUTES } from '@/constants';
import { ArrowRight, FileText, History, Sparkles, Upload } from 'lucide-react';
import Link from 'next/link';

/**
 * Candidate Resume Page
 *
 * Landing page for the resume section.
 * Options: Build with AIVI bot or upload PDF.
 * Also shows resume history (placeholder for now).
 *
 * Full chat UI will be implemented in Step 3.6.
 */
export default function CandidateResumePage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1
          className="text-2xl sm:text-3xl font-bold"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Your Resume
        </h1>
        <p className="text-sm sm:text-base mt-1" style={{ color: 'var(--neutral-gray)' }}>
          Build or upload your resume to get matched with the best jobs
        </p>
      </div>

      {/* Resume Creation Options */}
      <div className="grid sm:grid-cols-2 gap-4">
        {/* Build with AIVI */}
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_RESUME_NEW}
          className="glass-card rounded-2xl p-6 transition-all hover:scale-[1.02] hover:shadow-lg group"
        >
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
            style={{
              background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)',
            }}
          >
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h3
            className="text-lg font-semibold mb-2"
            style={{ color: 'var(--neutral-dark)' }}
          >
            Build with AIVI Bot
          </h3>
          <p className="text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
            Our AI assistant will guide you through creating a professional resume step by
            step, tailored to your industry.
          </p>
          <span
            className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors"
            style={{ color: 'var(--primary)' }}
          >
            Start Building
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </span>
        </Link>

        {/* Upload PDF */}
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_RESUME_NEW}
          className="glass-card rounded-2xl p-6 transition-all hover:scale-[1.02] hover:shadow-lg group"
        >
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
            style={{
              background: 'linear-gradient(135deg, #14B8A6 0%, #22C55E 100%)',
            }}
          >
            <Upload className="w-7 h-7 text-white" />
          </div>
          <h3
            className="text-lg font-semibold mb-2"
            style={{ color: 'var(--neutral-dark)' }}
          >
            Upload Resume PDF
          </h3>
          <p className="text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
            Already have a resume? Upload it and we&apos;ll extract the details. We&apos;ll
            only ask about any missing information.
          </p>
          <span
            className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors"
            style={{ color: 'var(--secondary-teal)' }}
          >
            Upload PDF
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </span>
        </Link>
      </div>

      {/* Resume History */}
      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5" style={{ color: 'var(--neutral-gray)' }} />
          <h2
            className="text-base font-semibold"
            style={{ color: 'var(--neutral-dark)' }}
          >
            Resume History
          </h2>
        </div>

        {/* Empty state */}
        <div className="text-center py-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-3"
            style={{ background: 'rgba(124, 58, 237, 0.1)' }}
          >
            <FileText className="w-7 h-7" style={{ color: 'var(--primary)' }} />
          </div>
          <p
            className="text-sm font-medium mb-1"
            style={{ color: 'var(--neutral-dark)' }}
          >
            No resume yet
          </p>
          <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
            Create your first resume using AIVI bot or upload a PDF
          </p>
        </div>
      </div>
    </div>
  );
}
