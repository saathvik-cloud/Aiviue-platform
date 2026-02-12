'use client';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/modal';
import { SelectDropdown } from '@/components/ui/select-dropdown';
import { useCandidateResumes, useApplyToJob } from '@/lib/hooks';
import { useCandidateAuthStore } from '@/stores';
import { formatDate } from '@/lib/utils';
import { getErrorMessage } from '@/lib/api';
import { ROUTES } from '@/constants';
import { FileText, Loader2, Send } from 'lucide-react';
import Link from 'next/link';
import { useState, useCallback, useEffect } from 'react';
import { toast } from 'sonner';

interface ApplyWithResumeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  jobId: string;
  jobTitle?: string;
  onSuccess?: () => void;
}

export function ApplyWithResumeModal({
  open,
  onOpenChange,
  jobId,
  jobTitle,
  onSuccess,
}: ApplyWithResumeModalProps) {
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const { data: resumes, isLoading: resumesLoading } = useCandidateResumes(
    candidate?.id
  );
  const applyMutation = useApplyToJob();
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');

  // Show all resumes (completed and in-progress) so user can choose any version
  const allResumes = resumes ?? [];
  const resumeOptions = allResumes.map((r) => ({
    value: r.id,
    label: `Resume v${r.version_number} – ${
      r.source === 'pdf_upload' ? 'Uploaded PDF' : 'Built with AIVI'
    } · ${formatDate(r.created_at)}`,
  }));

  // Reset selection when modal opens; default to first (most recent) resume
  useEffect(() => {
    if (open) {
      const list = resumes ?? [];
      setSelectedResumeId(list[0]?.id ?? '');
    }
  }, [open, resumes]);

  const handleApply = useCallback(async () => {
    if (!selectedResumeId) return;
    try {
      const res = await applyMutation.mutateAsync({
        jobId,
        data: { resume_id: selectedResumeId },
      });
      toast.success(
        res.already_applied ? 'Already applied' : 'Application submitted!'
      );
      onSuccess?.();
      onOpenChange(false);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  }, [jobId, selectedResumeId, applyMutation, onSuccess, onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Apply for this job</DialogTitle>
          <DialogDescription>
            {jobTitle ? (
              <>
                Choose which resume to send for <strong>{jobTitle}</strong>.
              </>
            ) : (
              'Choose which resume to attach to your application.'
            )}
          </DialogDescription>
        </DialogHeader>

        {resumesLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin" style={{ color: 'var(--primary)' }} />
          </div>
        ) : allResumes.length === 0 ? (
          <div className="py-4 space-y-4">
            <div
              className="flex items-center gap-3 p-4 rounded-xl"
              style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.2)',
              }}
            >
              <FileText className="w-10 h-10 flex-shrink-0" style={{ color: 'var(--status-draft)' }} />
              <div>
                <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                  No resumes yet
                </p>
                <p className="text-xs mt-0.5" style={{ color: 'var(--neutral-gray)' }}>
                  Build or upload at least one resume before applying.
                </p>
              </div>
            </div>
            <Link
              href={ROUTES.CANDIDATE_DASHBOARD_RESUME}
              className="btn-gradient inline-flex items-center justify-center gap-2 w-full py-3 rounded-xl text-sm font-semibold"
            >
              Go to Resume
            </Link>
          </div>
        ) : (
          <div className="space-y-4 py-2">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Select resume
              </label>
              <SelectDropdown
                options={resumeOptions}
                value={selectedResumeId}
                onChange={setSelectedResumeId}
                placeholder="Choose a resume..."
                className="w-full"
              />
            </div>
            <DialogFooter>
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-medium transition-colors"
                style={{ color: 'var(--neutral-gray)' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleApply}
                disabled={applyMutation.isPending}
                className="btn-gradient inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-70"
              >
                {applyMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                Apply
              </button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
