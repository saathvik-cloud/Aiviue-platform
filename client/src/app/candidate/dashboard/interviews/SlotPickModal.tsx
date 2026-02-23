'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getOfferWithSlots, pickSlot, candidateCancel } from '@/services/interview-scheduling.service';
import { getErrorMessage } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import { Loader2, X } from 'lucide-react';
import { useEffect } from 'react';
import { toast } from 'sonner';

export function SlotPickModal({
  scheduleId,
  onClose,
}: {
  scheduleId: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['interview-offer', scheduleId],
    queryFn: () => getOfferWithSlots(scheduleId),
    enabled: !!scheduleId,
  });

  const pickMutation = useMutation({
    mutationFn: (slotId: string) => pickSlot(scheduleId, { slot_id: slotId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-scheduling', 'candidate-offers'] });
      queryClient.invalidateQueries({ queryKey: ['interview-offer', scheduleId] });
      toast.success('Slot selected. Waiting for employer to confirm.');
      onClose();
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  const cancelMutation = useMutation({
    mutationFn: () => candidateCancel(scheduleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-scheduling', 'candidate-offers'] });
      toast.success('Offer cancelled.');
      onClose();
    },
    onError: (e) => toast.error(getErrorMessage(e)),
  });

  useEffect(() => {
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [onClose]);

  const slots = data?.slots?.filter((s) => s.status === 'offered') ?? [];

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/40 backdrop-blur-sm safe-area-inset-bottom"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full max-h-[90vh] sm:max-h-[85vh] flex flex-col rounded-t-2xl sm:rounded-2xl p-4 sm:p-6 shadow-xl overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(255,255,255,0.98) 0%, rgba(250, 245, 255, 0.95) 100%)',
          border: '1px solid rgba(124, 58, 237, 0.15)',
          maxWidth: '28rem',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4 flex-shrink-0">
          <h2 className="text-base sm:text-lg font-bold" style={{ color: 'var(--neutral-dark)' }}>
            Choose a slot
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2.5 -m-2.5 rounded-xl hover:bg-white/60 active:bg-white/70 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center touch-manipulation"
            style={{ color: 'var(--neutral-gray)' }}
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center gap-2 py-8 text-sm min-h-[120px]" style={{ color: 'var(--neutral-gray)' }}>
            <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />
            Loading slots…
          </div>
        ) : slots.length === 0 ? (
          <p className="text-sm py-4" style={{ color: 'var(--neutral-gray)' }}>
            No slots available to pick.
          </p>
        ) : (
          <div className="space-y-2 overflow-y-auto overflow-x-hidden flex-1 min-h-0 overscroll-contain -webkit-overflow-scrolling-touch max-h-[50vh] sm:max-h-64">
            {slots.map((slot) => (
              <button
                key={slot.id}
                type="button"
                onClick={() => pickMutation.mutate(slot.id)}
                disabled={pickMutation.isPending}
                className="w-full text-left px-4 py-3.5 sm:py-3 rounded-xl text-sm font-medium transition-colors hover:bg-white/80 active:bg-white/90 min-h-[48px] touch-manipulation"
                style={{
                  color: 'var(--neutral-dark)',
                  border: '1px solid rgba(124, 58, 237, 0.2)',
                }}
              >
                {pickMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
                    Selecting…
                  </span>
                ) : (
                  <span className="break-words">
                    {formatDateTime(slot.slot_start_utc)} – {formatDateTime(slot.slot_end_utc)}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        <div className="mt-4 pt-4 border-t flex-shrink-0" style={{ borderColor: 'var(--neutral-border)' }}>
          <button
            type="button"
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
            className="text-sm font-medium min-h-[44px] flex items-center touch-manipulation w-full sm:w-auto"
            style={{ color: 'var(--status-closed)' }}
          >
            {cancelMutation.isPending ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
                Cancelling…
              </span>
            ) : (
              'Cancel this offer'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
