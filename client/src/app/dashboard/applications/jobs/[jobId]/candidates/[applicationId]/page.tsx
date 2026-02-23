'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ROUTES, PRIMARY_GRADIENT } from '@/constants';
import { useApplicationDetail } from '@/lib/hooks';
import { formatDate, formatDateTime } from '@/lib/utils';
import { getErrorMessage } from '@/lib/api';
import {
  getScheduleForApplication,
  getAvailableSlotsForApplication,
  sendOffer,
  employerConfirmSlot,
  employerCancel,
} from '@/services/interview-scheduling.service';
import { LoadingContent } from '@/components/ui/loading-content';
import {
  ArrowLeft,
  Calendar,
  CalendarCheck,
  Download,
  FileText,
  Loader2,
  Mail,
  MapPin,
  Phone,
  User,
  XCircle,
} from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

const RESUME_CARD_STYLE = {
  background:
    'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.9) 50%, rgba(237, 233, 254, 0.85) 100%)',
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.7)',
  boxShadow:
    '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
} as const;
const BULLET_COLOR = '#7C3AED';
const TEXT_DARK = '#374151';
const TEXT_MUTED = '#6B7280';

function ResumeValue({ value }: { value: unknown }) {
  if (value == null || value === '') return null;
  if (Array.isArray(value)) {
    return (
      <ul className="space-y-2 list-none pl-0">
        {value.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5">
            <span
              className="w-1.5 h-1.5 rounded-full mt-2 shrink-0"
              style={{ backgroundColor: BULLET_COLOR }}
            />
            <span
              className="text-sm font-medium leading-relaxed"
              style={{ color: TEXT_DARK }}
            >
              {typeof item === 'object' && item !== null ? (
                <ResumeValue value={item} />
              ) : (
                String(item)
              )}
            </span>
          </li>
        ))}
      </ul>
    );
  }
  if (typeof value === 'object') {
    return (
      <div
        className="pl-3 sm:pl-4 border-l-2 space-y-2"
        style={{ borderColor: 'rgba(124, 58, 237, 0.25)' }}
      >
        {Object.entries(value).map(([k, v]) => (
          <div key={k}>
            <span
              className="text-xs font-semibold uppercase tracking-wide capitalize"
              style={{ color: TEXT_MUTED }}
            >
              {k.replace(/_/g, ' ')}:
            </span>{' '}
            <span className="text-sm font-medium" style={{ color: TEXT_DARK }}>
              <ResumeValue value={v} />
            </span>
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

function renderResumeSections(data: Record<string, unknown> | null) {
  if (!data) return null;
  const meta = (data.meta as Record<string, unknown>) || {};
  const sections = (data.sections as Record<string, unknown>) || {};
  const hasContent =
    Object.keys(meta).length > 0 || Object.keys(sections).length > 0;
  if (!hasContent) return null;

  return (
    <div className="relative space-y-6 sm:space-y-8">
      {Object.keys(sections).length > 0 && (
        <div className="space-y-6 sm:space-y-8">
          {Object.entries(sections).map(([sectionKey, sectionValue]) => (
            <section key={sectionKey}>
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <div
                  className="w-2 h-6 rounded-full shrink-0"
                  style={{ background: PRIMARY_GRADIENT }}
                />
                <h2
                  className="text-base sm:text-lg font-bold capitalize"
                  style={{ color: TEXT_DARK }}
                >
                  {sectionKey.replace(/_/g, ' ')}
                </h2>
              </div>
              <div className="ml-1">
                <ResumeValue value={sectionValue} />
              </div>
            </section>
          ))}
        </div>
      )}
      {Object.keys(meta).length > 0 && (
        <section
          className="pt-4 sm:pt-6 border-t"
          style={{ borderColor: 'rgba(124, 58, 237, 0.2)' }}
        >
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-2 h-5 rounded-full shrink-0"
              style={{ background: PRIMARY_GRADIENT }}
            />
            <h2
              className="text-xs font-semibold uppercase tracking-wide"
              style={{ color: TEXT_MUTED }}
            >
              Meta
            </h2>
          </div>
          <div
            className="text-xs space-y-1.5 font-medium"
            style={{ color: TEXT_MUTED }}
          >
            {Object.entries(meta).map(([k, v]) => (
              <div key={k}>
                <span className="capitalize">{k.replace(/_/g, ' ')}:</span>{' '}
                <ResumeValue value={v} />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/** Schedule interview: send slots or show status + confirm/cancel */
function ScheduleInterviewSection({
  jobId,
  applicationId,
}: {
  jobId: string;
  applicationId: string;
}) {
  const queryClient = useQueryClient();
  const [showSlotPicker, setShowSlotPicker] = useState(false);
  const [selectedSlots, setSelectedSlots] = useState<{ start_utc: string; end_utc: string }[]>([]);

  const { data: schedule, isLoading: scheduleLoading } = useQuery({
    queryKey: ['interview-schedule', applicationId],
    queryFn: () => getScheduleForApplication(applicationId),
  });

  const { data: availableSlots = [], isLoading: slotsLoading } = useQuery({
    queryKey: ['interview-available-slots', applicationId],
    queryFn: () => getAvailableSlotsForApplication(applicationId),
    enabled: showSlotPicker,
  });

  const sendOfferMutation = useMutation({
    mutationFn: () => sendOffer(applicationId, { slots: selectedSlots }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-schedule', applicationId] });
      setShowSlotPicker(false);
      setSelectedSlots([]);
      toast.success('Interview slots sent to candidate.');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const confirmMutation = useMutation({
    mutationFn: () => employerConfirmSlot(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-schedule', applicationId] });
      toast.success('Interview confirmed. Meet link created.');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const cancelMutation = useMutation({
    mutationFn: () => employerCancel(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-schedule', applicationId] });
      toast.success('Interview cancelled.');
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const toggleSlot = (slot: { start_utc: string; end_utc: string }) => {
    setSelectedSlots((prev) => {
      const exists = prev.some((s) => s.start_utc === slot.start_utc && s.end_utc === slot.end_utc);
      if (exists) return prev.filter((s) => !(s.start_utc === slot.start_utc && s.end_utc === slot.end_utc));
      return [...prev, slot];
    });
  };

  const stateLabels: Record<string, string> = {
    slots_offered: 'Slots sent – waiting for candidate',
    candidate_picked_slot: 'Candidate chose a slot',
    employer_confirmed: 'Confirmed',
    scheduled: 'Scheduled',
    cancelled: 'Cancelled',
  };

  if (scheduleLoading) {
    return (
      <div className="glass-card rounded-xl sm:rounded-2xl p-4 sm:p-6">
        <div className="flex items-center gap-2 text-sm min-h-[44px]" style={{ color: 'var(--neutral-gray)' }}>
          <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
          Loading schedule…
        </div>
      </div>
    );
  }

  if (!schedule) {
    return (
      <div className="glass-card rounded-xl sm:rounded-2xl p-4 sm:p-6">
        <h2 className="text-base sm:text-lg font-bold mb-2" style={{ color: 'var(--neutral-dark)' }}>
          Schedule interview
        </h2>
        <p className="text-xs sm:text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
          Send available time slots to the candidate. Set your availability first in Interview availability.
        </p>
        {!showSlotPicker ? (
          <button
            type="button"
            onClick={() => setShowSlotPicker(true)}
            className="btn-gradient inline-flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] px-4 py-3 rounded-xl text-sm font-semibold touch-manipulation"
          >
            <Calendar className="w-4 h-4 flex-shrink-0" />
            Send interview slots
          </button>
        ) : (
          <div className="space-y-4">
            {slotsLoading ? (
              <div className="flex items-center gap-2 text-sm min-h-[44px]" style={{ color: 'var(--neutral-gray)' }}>
                <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
                Loading slots…
              </div>
            ) : availableSlots.length === 0 ? (
              <p className="text-xs sm:text-sm" style={{ color: 'var(--neutral-gray)' }}>
                No slots available. Set your interview availability (working days and time window).
              </p>
            ) : (
              <>
                <p className="text-xs sm:text-sm" style={{ color: 'var(--neutral-gray)' }}>
                  Select one or more slots to offer (UTC):
                </p>
                <div className="max-h-40 sm:max-h-48 overflow-y-auto overflow-x-hidden space-y-1 overscroll-contain -webkit-overflow-scrolling-touch">
                  {availableSlots.map((slot) => {
                    const selected = selectedSlots.some(
                      (s) => s.start_utc === slot.start_utc && s.end_utc === slot.end_utc
                    );
                    return (
                      <label
                        key={`${slot.start_utc}-${slot.end_utc}`}
                        className="flex items-center gap-3 p-3 sm:p-2 rounded-lg cursor-pointer hover:bg-white/60 active:bg-white/70 min-h-[44px] sm:min-h-0 touch-manipulation"
                      >
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => toggleSlot(slot)}
                          className="w-5 h-5 sm:w-4 sm:h-4 flex-shrink-0 rounded"
                        />
                        <span className="text-xs sm:text-sm break-words" style={{ color: 'var(--neutral-dark)' }}>
                          {formatDateTime(slot.start_utc)} – {formatDateTime(slot.end_utc)}
                        </span>
                      </label>
                    );
                  })}
                </div>
                <div className="flex flex-col sm:flex-row flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => sendOfferMutation.mutate()}
                    disabled={selectedSlots.length === 0 || sendOfferMutation.isPending}
                    className="btn-gradient inline-flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] px-4 py-3 rounded-xl text-sm font-semibold touch-manipulation"
                  >
                    {sendOfferMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <CalendarCheck className="w-4 h-4" />
                    )}
                    Send offer
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowSlotPicker(false);
                      setSelectedSlots([]);
                    }}
                    className="btn-glass w-full sm:w-auto min-h-[44px] px-4 py-3 rounded-xl text-sm font-medium touch-manipulation"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  const isCancelled = schedule.state === 'cancelled';
  const canConfirm = schedule.state === 'candidate_picked_slot';

  return (
    <div className="glass-card rounded-xl sm:rounded-2xl p-4 sm:p-6">
      <h2 className="text-base sm:text-lg font-bold mb-2" style={{ color: 'var(--neutral-dark)' }}>
        Schedule interview
      </h2>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        <span
          className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium"
          style={{
            backgroundColor: isCancelled ? 'rgba(239,68,68,0.12)' : 'var(--primary-50)',
            color: isCancelled ? 'var(--status-closed)' : 'var(--primary)',
          }}
        >
          <Calendar className="w-3.5 h-3.5 sm:w-4 sm:h-4 flex-shrink-0" />
          <span className="break-words">{stateLabels[schedule.state] ?? schedule.state}</span>
        </span>
        {schedule.chosen_slot_start_utc && schedule.chosen_slot_end_utc && !isCancelled && (
          <span className="text-xs sm:text-sm w-full sm:w-auto" style={{ color: 'var(--neutral-gray)' }}>
            {formatDateTime(schedule.chosen_slot_start_utc)} – {formatDateTime(schedule.chosen_slot_end_utc)}
          </span>
        )}
        {schedule.meeting_link && (
          <a
            href={schedule.meeting_link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs sm:text-sm font-medium inline-flex items-center min-h-[44px] sm:min-h-0 touch-manipulation"
            style={{ color: 'var(--primary)' }}
          >
            Join Meet
          </a>
        )}
      </div>
      <div className="flex flex-col sm:flex-row flex-wrap gap-2 mt-3">
        {canConfirm && (
          <button
            type="button"
            onClick={() => confirmMutation.mutate()}
            disabled={confirmMutation.isPending}
            className="btn-gradient inline-flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] px-4 py-3 rounded-xl text-sm font-semibold touch-manipulation"
          >
            {confirmMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CalendarCheck className="w-4 h-4" />
            )}
            Confirm slot (create Meet link)
          </button>
        )}
        {!isCancelled && (
          <button
            type="button"
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
            className="inline-flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] px-4 py-3 rounded-xl text-sm font-medium border touch-manipulation"
            style={{ color: 'var(--status-closed)', borderColor: 'var(--status-closed)' }}
          >
            {cancelMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <XCircle className="w-4 h-4" />
            )}
            Cancel interview
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Application Management - Page 3: Candidate profile + resume card + download
 */
export default function ApplicationCandidateDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;
  const applicationId = params.applicationId as string;

  const { data: application, isLoading, isError } = useApplicationDetail(
    jobId,
    applicationId
  );

  if (!isLoading && (isError || !application)) {
    router.replace(ROUTES.APPLICATIONS_JOB(jobId));
    return null;
  }

  const candidate = application?.candidate;
  const resume = application?.resume;
  const resumePdfUrl = application?.resume_pdf_url;
  const resumeSnapshot = application?.resume_snapshot;

  // Resolve resume data: platform resume.resume_data, or screening resume_snapshot
  const resumeData =
    (resume?.resume_data as Record<string, unknown>) || resumeSnapshot || null;
  const pdfUrl = resume?.pdf_url || resumePdfUrl;

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href={ROUTES.APPLICATIONS_JOB(jobId)}
        className="inline-flex items-center gap-2 text-sm font-medium transition-colors hover:opacity-80"
        style={{ color: 'var(--primary)' }}
      >
        <ArrowLeft className="w-4 h-4" />
        Back to applicants
      </Link>

      <LoadingContent
        isLoading={isLoading}
        isEmpty={false}
        skeletonCount={1}
        renderSkeleton={
          <div className="space-y-6">
            <div className="glass-card rounded-2xl p-6 animate-pulse">
              <div className="h-8 rounded w-1/3 mb-4 bg-white/60" />
              <div className="h-4 rounded w-1/2 bg-white/50" />
            </div>
            <div
              className="rounded-2xl p-6 animate-pulse"
              style={RESUME_CARD_STYLE}
            >
              <div className="h-6 rounded w-full mb-4" style={{ background: 'rgba(124, 58, 237, 0.1)' }} />
              <div className="h-4 rounded w-3/4 mb-2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
              <div className="h-4 rounded w-1/2" style={{ background: 'rgba(124, 58, 237, 0.08)' }} />
            </div>
          </div>
        }
      >
        {/* Candidate profile card */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0"
              style={{
                background:
                  'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.12) 100%)',
              }}
            >
              {candidate?.profile_photo_url ? (
                <img
                  src={candidate.profile_photo_url}
                  alt={candidate.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <User className="w-8 h-8" style={{ color: 'var(--primary)' }} />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h1
                className="text-xl font-bold truncate"
                style={{ color: 'var(--neutral-dark)' }}
              >
                {candidate?.name ?? 'Candidate'}
              </h1>
              <p
                className="text-sm mt-1"
                style={{ color: 'var(--neutral-gray)' }}
              >
                Applied {application ? formatDate(application.applied_at) : ''}
              </p>
              <div className="flex flex-wrap gap-4 mt-4 text-sm">
                {candidate?.mobile && (
                  <span
                    className="flex items-center gap-2"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    <Phone className="w-4 h-4" />
                    {candidate.mobile}
                  </span>
                )}
                {candidate?.email && (
                  <span
                    className="flex items-center gap-2"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    <Mail className="w-4 h-4" />
                    {candidate.email}
                  </span>
                )}
                {candidate?.current_location && (
                  <span
                    className="flex items-center gap-2"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    <MapPin className="w-4 h-4" />
                    {candidate.current_location}
                  </span>
                )}
              </div>
              {candidate?.about && (
                <p
                  className="mt-4 text-sm leading-relaxed"
                  style={{ color: 'var(--neutral-gray)' }}
                >
                  {candidate.about}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Schedule interview */}
        <ScheduleInterviewSection
          jobId={jobId}
          applicationId={applicationId}
        />

        {/* Resume card + download */}
        <div
          className="rounded-2xl p-5 sm:p-6 lg:p-8 relative overflow-hidden"
          style={RESUME_CARD_STYLE}
        >
          <div
            className="absolute top-0 right-0 w-32 sm:w-40 h-32 sm:h-40 opacity-20 blur-3xl pointer-events-none"
            style={{
              background:
                'radial-gradient(circle, rgba(124, 58, 237, 0.35) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute bottom-0 left-0 w-24 sm:w-28 h-24 sm:h-28 opacity-15 blur-2xl pointer-events-none"
            style={{
              background:
                'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)',
            }}
          />

          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <h2
              className="text-lg font-bold"
              style={{ color: 'var(--neutral-dark)' }}
            >
              Resume
            </h2>
            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
              >
                <Download className="w-4 h-4" />
                Download PDF
              </a>
            )}
          </div>

          {!resumeData ||
          (Object.keys((resumeData as Record<string, unknown>).sections || {}).length === 0 &&
            Object.keys((resumeData as Record<string, unknown>).meta || {}).length === 0) ? (
            <div className="relative flex flex-col items-center justify-center py-12 sm:py-16 text-center">
              <FileText
                className="w-12 h-12 mb-3"
                style={{ color: BULLET_COLOR }}
              />
              <p className="text-sm font-medium" style={{ color: TEXT_MUTED }}>
                No structured resume content available.
              </p>
              {pdfUrl && (
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 btn-gradient inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold"
                >
                  <Download className="w-4 h-4" /> Open PDF
                </a>
              )}
            </div>
          ) : (
            <div className="relative">
              {renderResumeSections(resumeData as Record<string, unknown>)}
            </div>
          )}
        </div>
      </LoadingContent>
    </div>
  );
}
