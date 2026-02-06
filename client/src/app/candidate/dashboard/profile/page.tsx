'use client';

import { User } from 'lucide-react';

/**
 * Candidate Profile Page - Placeholder
 *
 * Full profile management (photo upload, email, DOB, Aadhaar/PAN,
 * languages, about, salary) will be implemented in Step 3.7.
 */
export default function CandidateProfilePage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div
          className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4"
          style={{ background: 'rgba(20, 184, 166, 0.1)' }}
        >
          <User className="w-10 h-10" style={{ color: 'var(--secondary-teal)' }} />
        </div>
        <h2
          className="text-xl font-bold mb-2"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Profile Management
        </h2>
        <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
          Full profile editor coming in Step 3.7
        </p>
      </div>
    </div>
  );
}
