'use client';

import { useQuery } from '@tanstack/react-query';
import { ROUTES } from '@/constants';
import { listMyOffers } from '@/services/interview-scheduling.service';
import { formatDateTime } from '@/lib/utils';
import { LoadingContent } from '@/components/ui/loading-content';
import { CalendarCheck, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import type { InterviewScheduleResponse } from '@/types';
import { SlotPickModal } from './SlotPickModal';

const STATE_LABELS: Record<string, string> = {
  slots_offered: 'Choose a slot',
  candidate_picked_slot: 'Waiting for employer',
  employer_confirmed: 'Confirmed',
  scheduled: 'Scheduled',
  cancelled: 'Cancelled',
};

export default function CandidateInterviewsPage() {
  const [modalScheduleId, setModalScheduleId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['interview-scheduling', 'candidate-offers'],
    queryFn: listMyOffers,
  });

  const items = data?.items ?? [];

  return (
    <div className="w-full space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
          Interview offers
        </h1>
        <p className="text-xs sm:text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>
          View and pick time slots for your interviews.
        </p>
      </div>

      <LoadingContent
        isLoading={isLoading}
        isEmpty={items.length === 0}
        skeletonCount={3}
        renderSkeleton={
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="rounded-2xl p-5 animate-pulse h-28"
                style={{
                  background: 'linear-gradient(145deg, rgba(250, 245, 255, 0.6) 0%, rgba(243, 232, 255, 0.5) 100%)',
                  border: '1px solid rgba(255, 255, 255, 0.5)',
                }}
              >
                <div className="h-4 bg-white/60 rounded w-1/3 mb-2" />
                <div className="h-3 bg-white/50 rounded w-1/2" />
              </div>
            ))}
          </div>
        }
        emptyContent={
          <div className="text-center py-16 px-4">
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{
                background:
                  'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
              }}
            >
              <CalendarCheck className="w-10 h-10" style={{ color: 'var(--primary)' }} />
            </div>
            <p className="text-lg font-medium mb-1" style={{ color: 'var(--neutral-dark)' }}>
              No interview offers yet
            </p>
            <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
              When employers send you time slots, they will appear here.
            </p>
            <Link
              href={ROUTES.CANDIDATE_DASHBOARD_JOBS}
              className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium mt-4"
            >
              Browse jobs
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        }
      >
        <div className="space-y-3">
          {items.map((schedule) => (
            <InterviewOfferCard
              key={schedule.id}
              schedule={schedule}
              onPickSlot={() => setModalScheduleId(schedule.id)}
            />
          ))}
        </div>
      </LoadingContent>

      {modalScheduleId && (
        <SlotPickModal
          scheduleId={modalScheduleId}
          onClose={() => setModalScheduleId(null)}
        />
      )}
    </div>
  );
}

function InterviewOfferCard({
  schedule,
  onPickSlot,
}: {
  schedule: InterviewScheduleResponse;
  onPickSlot: () => void;
}) {
  const stateLabel = STATE_LABELS[schedule.state] ?? schedule.state;
  const isCancelled = schedule.state === 'cancelled';
  const canPickSlot = schedule.state === 'slots_offered';
  const hasChosenSlot = !!schedule.chosen_slot_start_utc && !!schedule.chosen_slot_end_utc;

  return (
    <div
      className="rounded-xl sm:rounded-2xl p-4 sm:p-5 transition-all hover:shadow-lg"
      style={{
        background:
          'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.9) 50%, rgba(237, 233, 254, 0.85) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.7)',
        boxShadow: '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
      }}
    >
      <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold" style={{ color: 'var(--neutral-dark)' }}>
            Interview offer
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-1">
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
              style={{
                backgroundColor: isCancelled ? 'rgba(239,68,68,0.12)' : 'rgba(124, 58, 237, 0.12)',
                color: isCancelled ? 'var(--status-closed)' : 'var(--primary)',
              }}
            >
              <CalendarCheck className="w-3.5 h-3.5 flex-shrink-0" />
              {stateLabel}
            </span>
            {hasChosenSlot && !isCancelled && (
              <span className="text-xs block sm:inline mt-1 sm:mt-0" style={{ color: 'var(--neutral-gray)' }}>
                {formatDateTime(schedule.chosen_slot_start_utc!)} –{' '}
                {formatDateTime(schedule.chosen_slot_end_utc!)}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center shrink-0 gap-2 flex-wrap">
          {schedule.meeting_link && !isCancelled && (
            <a
              href={schedule.meeting_link}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-gradient inline-flex items-center justify-center gap-2 min-h-[44px] px-4 py-3 rounded-xl text-sm font-semibold touch-manipulation"
            >
              Join Meet
            </a>
          )}
          {canPickSlot && (
            <button
              type="button"
              onClick={onPickSlot}
              className="btn-gradient inline-flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] px-4 py-3 rounded-xl text-sm font-semibold touch-manipulation"
            >
              Pick slot
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
