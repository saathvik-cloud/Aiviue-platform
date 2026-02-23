'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getErrorMessage } from '@/lib/api';
import { getAvailability, setAvailability } from '@/services/interview-scheduling.service';
import type { EmployerAvailabilityCreate } from '@/types';
import { SLOT_DURATION_CHOICES, BUFFER_CHOICES } from '@/types';
import { SelectDropdown } from '@/components';
import { Input } from '@/components/ui/input';
import { LoadingContent } from '@/components/ui/loading-content';
import { CalendarClock, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']; // 0-6

function timeToInputValue(t: string | undefined): string {
  if (!t) return '09:00';
  const part = t.split(':');
  return `${part[0] ?? '09'}:${part[1] ?? '00'}`;
}

function inputValueToTime(v: string): string {
  return v.length >= 5 ? `${v}:00` : `${v}:00:00`;
}

export default function AvailabilityPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<EmployerAvailabilityCreate>({
    working_days: [0, 1, 2, 3, 4],
    start_time: '09:00:00',
    end_time: '17:00:00',
    timezone: 'Asia/Kolkata',
    slot_duration_minutes: 30,
    buffer_minutes: 10,
  });

  const { data: availability, isLoading } = useQuery({
    queryKey: ['interview-scheduling', 'availability'],
    queryFn: async () => {
      try {
        return await getAvailability();
      } catch (e: unknown) {
        if (typeof e === 'object' && e !== null && 'response' in e) {
          const ax = e as { response?: { status?: number } };
          if (ax.response?.status === 404) return null;
        }
        throw e;
      }
    },
  });

  useEffect(() => {
    if (availability) {
      setForm({
        working_days: availability.working_days,
        start_time: availability.start_time,
        end_time: availability.end_time,
        timezone: availability.timezone,
        slot_duration_minutes: availability.slot_duration_minutes,
        buffer_minutes: availability.buffer_minutes,
      });
    }
  }, [availability]);

  const saveMutation = useMutation({
    mutationFn: (body: EmployerAvailabilityCreate) => setAvailability(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-scheduling', 'availability'] });
      toast.success('Availability saved.');
    },
    onError: (e) => {
      toast.error(getErrorMessage(e));
    },
  });

  const handleWorkingDayToggle = (day: number) => {
    setForm((prev) => {
      const next = prev.working_days.includes(day)
        ? prev.working_days.filter((d) => d !== day)
        : [...prev.working_days, day].sort((a, b) => a - b);
      if (next.length === 0) return prev;
      return { ...prev, working_days: next };
    });
  };

  const handleSubmit = () => {
    if (form.working_days.length === 0) {
      toast.error('Select at least one working day.');
      return;
    }
    saveMutation.mutate(form);
  };

  const slotOptions = SLOT_DURATION_CHOICES.map((m) => ({
    value: String(m),
    label: `${m} min`,
  }));
  const bufferOptions = BUFFER_CHOICES.map((m) => ({
    value: String(m),
    label: `${m} min`,
  }));

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4 sm:space-y-6 px-0 sm:px-0">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>
          Interview availability
        </h1>
        <p className="text-xs sm:text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>
          Set your working window and slot length. Candidates will only see slots within this window.
        </p>
      </div>

      <LoadingContent
        isLoading={isLoading}
        isEmpty={false}
        skeletonCount={1}
        renderSkeleton={
          <div className="glass-card rounded-2xl p-6 animate-pulse">
            <div className="h-6 rounded w-1/3 mb-4 bg-white/60" />
            <div className="h-10 rounded w-full mb-4 bg-white/50" />
            <div className="h-10 rounded w-full bg-white/50" />
          </div>
        }
      >
        <div className="glass-card rounded-xl sm:rounded-2xl p-4 sm:p-6 space-y-4 sm:space-y-6">
          {/* Working days - touch-friendly checkboxes */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Working days
            </label>
            <div className="flex flex-wrap gap-x-4 gap-y-2 sm:gap-3">
              {WEEKDAY_LABELS.map((label, i) => (
                <label
                  key={i}
                  className="flex items-center gap-2 cursor-pointer min-h-[44px] sm:min-h-0 py-1 sm:py-0 touch-manipulation"
                  style={{ color: 'var(--neutral-gray)' }}
                >
                  <input
                    type="checkbox"
                    checked={form.working_days.includes(i)}
                    onChange={() => handleWorkingDayToggle(i)}
                    className="rounded border-neutral-border w-5 h-5 sm:w-4 sm:h-4 flex-shrink-0"
                  />
                  <span className="text-sm select-none">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Start / End time */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Start time
              </label>
              <Input
                type="time"
                value={timeToInputValue(form.start_time)}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, start_time: inputValueToTime(e.target.value) }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                End time
              </label>
              <Input
                type="time"
                value={timeToInputValue(form.end_time)}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, end_time: inputValueToTime(e.target.value) }))
                }
              />
            </div>
          </div>

          {/* Timezone */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Timezone
            </label>
            <Input
              value={form.timezone}
              onChange={(e) => setForm((prev) => ({ ...prev, timezone: e.target.value.trim() || 'Asia/Kolkata' }))}
              placeholder="e.g. Asia/Kolkata"
            />
          </div>

          {/* Slot duration & Buffer */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Slot duration
              </label>
              <SelectDropdown
                options={slotOptions}
                value={String(form.slot_duration_minutes)}
                onChange={(v) =>
                  setForm((prev) => ({ ...prev, slot_duration_minutes: Number(v) }))
                }
                placeholder="Select"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Buffer between slots
              </label>
              <SelectDropdown
                options={bufferOptions}
                value={String(form.buffer_minutes)}
                onChange={(v) => setForm((prev) => ({ ...prev, buffer_minutes: Number(v) }))}
                placeholder="Select"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={saveMutation.isPending}
              className="btn-gradient inline-flex items-center justify-center gap-2 w-full sm:w-auto min-h-[44px] px-5 py-3 sm:py-2.5 rounded-xl text-sm font-semibold touch-manipulation"
            >
              {saveMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CalendarClock className="w-4 h-4" />
              )}
              Save availability
            </button>
          </div>
        </div>
      </LoadingContent>
    </div>
  );
}
