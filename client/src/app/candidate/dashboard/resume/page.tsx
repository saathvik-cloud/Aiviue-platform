'use client';

import { CandidateChatContainer } from '@/components/candidate-chat';
import { useSearchParams } from 'next/navigation';

/**
 * Candidate Resume Page – taglines + AIVI chatbot only.
 * Resume history is in Dashboard Quick Actions → /candidate/dashboard/resume/history.
 */
export default function CandidateResumePage() {
  const searchParams = useSearchParams();
  const flowUpload = searchParams.get('flow') === 'upload';

  return (
    <div className="space-y-6 pb-8">
      {/* Tagline – gradient background + colorful heading */}
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
          Build your resume with AIVI bot step by step, or upload your existing PDF and we’ll
          extract the details. The AI assistant will guide you through any missing information.
        </p>
      </div>

      {/* Chatbot – directly visible, no extra click */}
      <div className="rounded-2xl overflow-hidden border border-[var(--neutral-border)] bg-white/90 backdrop-blur-sm">
        <CandidateChatContainer initialFlow={flowUpload ? 'upload' : undefined} />
      </div>

    </div>
  );
}
