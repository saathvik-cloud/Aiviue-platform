'use client';

import { ChatContainer } from '@/components';
import { ROUTES } from '@/constants';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

/**
 * New Job Page - AIVI Conversational Bot Interface
 * 
 * This page replaces the old static form with an interactive
 * chat experience powered by AIVI.
 */
export default function NewJobPage() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Back Button */}
      <Link
        href={ROUTES.JOBS}
        className="inline-flex items-center gap-2 text-sm font-medium mb-5 transition-colors hover:opacity-80"
        style={{ color: 'var(--neutral-gray)' }}
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Jobs
      </Link>

      {/* AIVI Chat Interface */}
      <ChatContainer />
    </div>
  );
}
