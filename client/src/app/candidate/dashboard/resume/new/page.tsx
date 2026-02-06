'use client';

import { CandidateChatContainer } from '@/components/candidate-chat';

/**
 * Resume Builder (New) Page
 *
 * This hosts the AIVI chat interface for building resumes.
 * Features:
 * - Real-time WebSocket communication
 * - PDF upload with extraction
 * - Step-by-step guided resume building
 * - Progress tracking
 */
export default function CandidateResumeNewPage() {
  return (
    <div className="h-full">
      <CandidateChatContainer />
    </div>
  );
}
