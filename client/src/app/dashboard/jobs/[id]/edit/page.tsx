'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';
import { ROUTES } from '@/constants';
import { useJob, useUpdateJob } from '@/lib/hooks';
import { SelectDropdown } from '@/components';
import type { UpdateJobRequest } from '@/types';
import { ArrowLeft, Loader2, CheckCircle, AlertCircle, Building, Wifi, Home } from 'lucide-react';

// Work type options with icons
const WORK_TYPE_OPTIONS = [
  { value: '', label: 'Select work type...' },
  { value: 'onsite', label: 'On-site', icon: <Building className="w-4 h-4" style={{ color: 'var(--primary)' }} /> },
  { value: 'remote', label: 'Remote', icon: <Wifi className="w-4 h-4" style={{ color: 'var(--secondary-teal)' }} /> },
  { value: 'hybrid', label: 'Hybrid', icon: <Home className="w-4 h-4" style={{ color: 'var(--accent)' }} /> },
];

/**
 * Edit Job Page - Glassmorphism design with custom dropdowns
 */
export default function EditJobPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const { data: job, isLoading } = useJob(jobId);
  const updateJob = useUpdateJob();
  const [formData, setFormData] = useState<Partial<UpdateJobRequest>>({});

  useEffect(() => {
    if (job) {
      setFormData({
        title: job.title,
        description: job.description,
        requirements: job.requirements || '',
        location: job.location || '',
        work_type: job.work_type,
        salary_range_min: job.salary_range_min,
        salary_range_max: job.salary_range_max,
        openings_count: job.openings_count,
        version: job.version,
      });
    }
  }, [job]);

  const handleFieldChange = (field: keyof UpdateJobRequest, value: unknown) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!formData.title || !formData.description) {
      toast.error('Title and description are required');
      return;
    }

    try {
      await updateJob.mutateAsync({ id: jobId, data: formData as UpdateJobRequest });
      toast.success('Job updated successfully!');
      router.push(ROUTES.JOB_DETAILS(jobId));
    } catch {
      toast.error('Failed to update job');
    }
  };

  const inputStyle = "w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2";

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-16">
        <div 
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
          style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%)' }}
        >
          <AlertCircle className="w-8 h-8" style={{ color: 'var(--status-closed)' }} />
        </div>
        <p className="text-lg font-medium" style={{ color: 'var(--neutral-dark)' }}>Job not found</p>
        <Link href={ROUTES.JOBS} className="inline-flex items-center gap-2 mt-4 text-sm font-medium gradient-text">
          <ArrowLeft className="w-4 h-4" />
          Back to Jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Link href={ROUTES.JOB_DETAILS(jobId)} className="inline-flex items-center gap-2 text-sm font-medium mb-6" style={{ color: 'var(--neutral-gray)' }}>
        <ArrowLeft className="w-4 h-4" />
        Back to Job Details
      </Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>Edit Job</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>Update the job details below</p>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Job Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.title || ''}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            className={inputStyle}
            style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Description <span className="text-red-500">*</span>
          </label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => handleFieldChange('description', e.target.value)}
            rows={6}
            className={`${inputStyle} resize-none`}
            style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Requirements</label>
          <textarea
            value={formData.requirements || ''}
            onChange={(e) => handleFieldChange('requirements', e.target.value)}
            rows={4}
            className={`${inputStyle} resize-none`}
            style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Location</label>
            <input
              type="text"
              value={formData.location || ''}
              onChange={(e) => handleFieldChange('location', e.target.value)}
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Work Type</label>
            <SelectDropdown
              options={WORK_TYPE_OPTIONS}
              value={formData.work_type || ''}
              onChange={(val) => handleFieldChange('work_type', val || undefined)}
              placeholder="Select work type..."
            />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Salary Min</label>
            <input
              type="number"
              value={formData.salary_range_min || ''}
              onChange={(e) => handleFieldChange('salary_range_min', e.target.value ? Number(e.target.value) : undefined)}
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Salary Max</label>
            <input
              type="number"
              value={formData.salary_range_max || ''}
              onChange={(e) => handleFieldChange('salary_range_max', e.target.value ? Number(e.target.value) : undefined)}
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>
        </div>

        <div className="sm:w-1/2">
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Number of Openings</label>
          <input
            type="number"
            value={formData.openings_count || 1}
            onChange={(e) => handleFieldChange('openings_count', Number(e.target.value) || 1)}
            min={1}
            className={inputStyle}
            style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
          />
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mt-6">
        <Link
          href={ROUTES.JOB_DETAILS(jobId)}
          className="btn-glass flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium"
          style={{ color: 'var(--neutral-dark)' }}
        >
          Cancel
        </Link>
        <button
          onClick={handleSubmit}
          disabled={updateJob.isPending || !formData.title || !formData.description}
          className="btn-gradient flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-medium disabled:opacity-50"
        >
          {updateJob.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              Save Changes
            </>
          )}
        </button>
      </div>
    </div>
  );
}
