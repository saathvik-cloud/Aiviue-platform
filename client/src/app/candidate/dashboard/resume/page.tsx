'use client';

import { ROUTES } from '@/constants';
import { CandidateChatContainer } from '@/components/candidate-chat';
import { History, FileUp, Sparkles, Target, Briefcase } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

const BANNER_TAGLINES = [
  { icon: FileUp, text: 'Upload your resume' },
  { icon: Target, text: "We'll recommend you jobs" },
  { icon: Briefcase, text: 'Get visible to employers' },
  { icon: Sparkles, text: 'Find your dream job' },
] as const;

/**
 * Candidate Resume Page – banner with taglines, Resume History button, and AIVI chatbot.
 * Resume history is also linked from Dashboard Quick Actions.
 */
export default function CandidateResumePage() {
  const searchParams = useSearchParams();
  const flowUpload = searchParams.get('flow') === 'upload';

  return (
    <div className="space-y-4 sm:space-y-5 pb-8">
      {/* Banner – gradient, headline, taglines with icons */}
      <div
        className="rounded-2xl p-5 sm:p-6 relative overflow-hidden"
        style={{
          background:
            'linear-gradient(135deg, rgba(253, 242, 248, 0.98) 0%, rgba(243, 232, 255, 0.9) 40%, rgba(237, 233, 254, 0.85) 100%)',
          border: '1px solid rgba(236, 72, 153, 0.12)',
          boxShadow: '0 4px 24px rgba(124, 58, 237, 0.08)',
          backdropFilter: 'blur(12px)',
        }}
      >
        <div
          className="absolute top-0 right-0 w-40 h-40 opacity-20 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(236, 72, 153, 0.35) 0%, rgba(124, 58, 237, 0.25) 50%, transparent 70%)' }}
        />
        <h1 className="text-xl sm:text-2xl font-bold gradient-text relative">
          Build or upload your resume to get matched with the best jobs
        </h1>
        <p className="text-sm mt-2 relative" style={{ color: 'var(--neutral-gray)' }}>
          Build your resume with AIVI step by step, or upload your existing PDF and we’ll
          extract the details. The AI assistant will guide you through any missing information.
        </p>
        {/* Taglines with icons */}
        <ul className="mt-4 sm:mt-5 flex flex-wrap gap-x-6 gap-y-2 sm:gap-y-3 relative">
          {BANNER_TAGLINES.map(({ icon: Icon, text }) => (
            <li key={text} className="flex items-center gap-2 text-sm" style={{ color: 'var(--neutral-gray)' }}>
              <span className="flex items-center justify-center w-7 h-7 rounded-lg shrink-0" style={{ background: 'rgba(124, 58, 237, 0.12)', color: '#7C3AED' }}>
                <Icon className="w-3.5 h-3.5" />
              </span>
              <span>{text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Resume History – right-aligned between tagline and chatbot (same as Dashboard quick action) */}
      <div className="flex justify-end">
        <Link
          href={ROUTES.CANDIDATE_DASHBOARD_RESUME_HISTORY}
          className="inline-flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 rounded-xl text-sm font-medium transition-all hover:scale-[1.02] active:scale-[0.98]"
          style={{
            background:
              'linear-gradient(135deg, rgba(255, 247, 237, 0.9) 0%, rgba(254, 215, 170, 0.4) 50%, rgba(251, 191, 36, 0.2) 100%)',
            border: '1px solid rgba(249, 115, 22, 0.15)',
            color: 'var(--neutral-dark)',
          }}
        >
          <History className="w-4 h-4 sm:w-5 sm:h-5 shrink-0" style={{ color: '#EA580C' }} />
          <span>Resume History</span>
        </Link>
      </div>

      {/* Chatbot – directly visible, no extra click */}
      <div className="rounded-2xl overflow-hidden border border-[var(--neutral-border)] bg-white/90 backdrop-blur-sm">
        <CandidateChatContainer initialFlow={flowUpload ? 'upload' : undefined} />
      </div>
    </div>
  );
}
