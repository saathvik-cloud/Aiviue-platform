'use client';

import { CandidateChatContainer } from '@/components/candidate-chat';
import { useSearchParams } from 'next/navigation';

/**
 * Resume Builder (New) Page
 *
 * This hosts the AIVI chat interface for building resumes.
 * Features:
 * - Real-time WebSocket communication
 * - PDF upload with extraction (?flow=upload for direct upload entry)
 * - Step-by-step guided resume building
 * - Progress tracking
 */
export default function CandidateResumeNewPage() {
  const searchParams = useSearchParams();
  const flowUpload = searchParams.get('flow') === 'upload';

  return (
    <div className="h-full">
      <CandidateChatContainer initialFlow={flowUpload ? 'upload' : undefined} />
    </div>
  );
}
