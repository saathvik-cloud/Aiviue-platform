'use client';

import { Briefcase } from 'lucide-react';

/**
 * Candidate Jobs Page - Placeholder
 *
 * Job recommendations and "Explore Jobs" functionality
 * will be implemented in Step 3.8.
 */
export default function CandidateJobsPage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div
          className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4"
          style={{
            background:
              'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)',
          }}
        >
          <Briefcase className="w-10 h-10" style={{ color: 'var(--primary)' }} />
        </div>
        <h2
          className="text-xl font-bold mb-2"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Job Recommendations
        </h2>
        <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
          Job matching and exploration coming in Step 3.8
        </p>
      </div>
    </div>
  );
}
