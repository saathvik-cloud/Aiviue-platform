'use client';

import { Sparkles } from 'lucide-react';

/**
 * Resume Builder (New) Page - Placeholder
 *
 * This will host the full AIVI chat interface for building resumes.
 * Full WebSocket-based chat UI will be implemented in Step 3.6.
 */
export default function CandidateResumeNewPage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div
          className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4"
          style={{
            background: 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)',
          }}
        >
          <Sparkles className="w-10 h-10 text-white" />
        </div>
        <h2
          className="text-xl font-bold mb-2"
          style={{ color: 'var(--neutral-dark)' }}
        >
          AIVI Resume Builder
        </h2>
        <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
          Chat interface coming in Step 3.6
        </p>
      </div>
    </div>
  );
}
