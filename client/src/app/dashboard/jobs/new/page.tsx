'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';
import { ROUTES, VALIDATION } from '@/constants';
import { useAuthStore } from '@/stores';
import { useSubmitExtraction, useExtraction, useCreateJob } from '@/lib/hooks';
import { SelectDropdown } from '@/components';
import type { CreateJobRequest } from '@/types';
import { 
  ArrowLeft,
  Sparkles,
  FileText,
  PenLine,
  ArrowRight,
  Loader2,
  CheckCircle,
  RefreshCw,
  Building,
  Wifi,
  Home
} from 'lucide-react';

type Step = 'choose' | 'paste' | 'extracting' | 'review' | 'manual';

// Work type options with icons
const WORK_TYPE_OPTIONS = [
  { value: '', label: 'Select work type...' },
  { value: 'onsite', label: 'On-site', icon: <Building className="w-4 h-4" style={{ color: 'var(--primary)' }} /> },
  { value: 'remote', label: 'Remote', icon: <Wifi className="w-4 h-4" style={{ color: 'var(--secondary-teal)' }} /> },
  { value: 'hybrid', label: 'Hybrid', icon: <Home className="w-4 h-4" style={{ color: 'var(--accent)' }} /> },
];

/**
 * New Job Page - AIVI Bot Wizard with glassmorphism design
 */
export default function NewJobPage() {
  const router = useRouter();
  const employer = useAuthStore((state) => state.employer);
  
  const [step, setStep] = useState<Step>('choose');
  const [rawJd, setRawJd] = useState('');
  const [extractionId, setExtractionId] = useState<string | null>(null);
  const [editedData, setEditedData] = useState<Partial<CreateJobRequest>>({});
  
  const submitExtraction = useSubmitExtraction();
  const { data: extraction } = useExtraction(extractionId ?? undefined);
  const createJob = useCreateJob();

  const handleSubmitJd = async () => {
    if (rawJd.length < VALIDATION.MIN_JD_LENGTH) {
      toast.error(`Job description must be at least ${VALIDATION.MIN_JD_LENGTH} characters`);
      return;
    }

    try {
      setStep('extracting');
      const result = await submitExtraction.mutateAsync({
        raw_jd: rawJd,
        employer_id: employer?.id,
      });
      setExtractionId(result.id);
    } catch {
      toast.error('Failed to submit job description');
      setStep('paste');
    }
  };

  if (extractionId && extraction) {
    if (extraction.status === 'completed' && step === 'extracting') {
      setEditedData({
        employer_id: employer?.id,
        title: extraction.extracted_data?.title || '',
        description: extraction.extracted_data?.description || '',
        requirements: extraction.extracted_data?.requirements || '',
        location: extraction.extracted_data?.location || '',
        work_type: extraction.extracted_data?.work_type as CreateJobRequest['work_type'],
        salary_range_min: extraction.extracted_data?.salary_range_min,
        salary_range_max: extraction.extracted_data?.salary_range_max,
        experience_min: extraction.extracted_data?.experience_min,
        experience_max: extraction.extracted_data?.experience_max,
        openings_count: extraction.extracted_data?.openings_count || 1,
      });
      setStep('review');
    } else if (extraction.status === 'failed' && step === 'extracting') {
      toast.error(extraction.error_message || 'Extraction failed');
      setStep('paste');
    }
  }

  const handleFieldChange = (field: keyof CreateJobRequest, value: unknown) => {
    setEditedData(prev => ({ ...prev, [field]: value }));
  };

  const handleCreateJob = async () => {
    if (!editedData.title || !editedData.description) {
      toast.error('Title and description are required');
      return;
    }

    try {
      const job = await createJob.mutateAsync(editedData as CreateJobRequest);
      toast.success('Job created successfully!');
      router.push(ROUTES.JOB_DETAILS(job.id));
    } catch {
      toast.error('Failed to create job');
    }
  };

  const handleReset = () => {
    setStep('choose');
    setRawJd('');
    setExtractionId(null);
    setEditedData({});
  };

  const inputStyle = "w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2";

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back Button */}
      <Link href={ROUTES.JOBS} className="inline-flex items-center gap-2 text-sm font-medium mb-6" style={{ color: 'var(--neutral-gray)' }}>
        <ArrowLeft className="w-4 h-4" />
        Back to Jobs
      </Link>

      {/* AIVI Bot Header */}
      <div className="glass-card rounded-2xl p-5 mb-6 relative overflow-hidden">
        {/* Background decoration */}
        <div 
          className="absolute top-0 right-0 w-32 h-32 rounded-full opacity-20 blur-2xl"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        
        <div className="flex items-center gap-4 relative">
          <div 
            className="w-14 h-14 rounded-2xl flex items-center justify-center animate-pulse-glow"
            style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
          >
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">AIVI Bot</h1>
            <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
              {step === 'choose' && "Let me help you create a job posting!"}
              {step === 'paste' && "Paste your job description below"}
              {step === 'extracting' && "Analyzing your job description..."}
              {step === 'review' && "Review the extracted details"}
              {step === 'manual' && "Fill in the job details"}
            </p>
          </div>
        </div>
      </div>

      {/* Step: Choose Mode */}
      {step === 'choose' && (
        <div className="grid sm:grid-cols-2 gap-4">
          <button
            onClick={() => setStep('paste')}
            className="glass-card rounded-2xl p-6 text-left transition-all"
          >
            <div 
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
            >
              <FileText className="w-7 h-7" style={{ color: 'var(--primary)' }} />
            </div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Paste Job Description
            </h3>
            <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
              Have a JD ready? Paste it and let AI extract all the details automatically.
            </p>
          </button>

          <button
            onClick={() => {
              setEditedData({ employer_id: employer?.id, openings_count: 1 });
              setStep('manual');
            }}
            className="glass-card rounded-2xl p-6 text-left transition-all"
          >
            <div 
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)' }}
            >
              <PenLine className="w-7 h-7" style={{ color: 'var(--accent)' }} />
            </div>
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Create Manually
            </h3>
            <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
              Fill in the job details step by step with AIVI&apos;s guidance.
            </p>
          </button>
        </div>
      )}

      {/* Step: Paste JD */}
      {step === 'paste' && (
        <div className="glass-card rounded-2xl p-6">
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Job Description
          </label>
          <textarea
            value={rawJd}
            onChange={(e) => setRawJd(e.target.value)}
            placeholder="Paste your job description here..."
            rows={12}
            className={`${inputStyle} resize-none`}
            style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
          />
          <p className="text-xs mt-2" style={{ color: 'var(--neutral-gray)' }}>
            {rawJd.length} / {VALIDATION.MIN_JD_LENGTH}+ characters
          </p>

          <div className="flex flex-col sm:flex-row gap-3 mt-6">
            <button
              onClick={() => setStep('choose')}
              className="btn-glass px-4 py-3 rounded-xl text-sm font-medium"
              style={{ color: 'var(--neutral-dark)' }}
            >
              Back
            </button>
            <button
              onClick={handleSubmitJd}
              disabled={rawJd.length < VALIDATION.MIN_JD_LENGTH || submitExtraction.isPending}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-medium text-white disabled:opacity-50 transition-colors hover:opacity-90"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              {submitExtraction.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Extract Details'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step: Extracting */}
      {step === 'extracting' && (
        <div className="glass-card rounded-2xl p-12 text-center">
          <div 
            className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6"
            style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
          >
            <Loader2 className="w-10 h-10 animate-spin" style={{ color: 'var(--primary)' }} />
          </div>
          <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Analyzing Job Description
          </h3>
          <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
            AIVI is extracting key details from your JD...
          </p>
        </div>
      )}

      {/* Step: Review & Manual - Form */}
      {(step === 'review' || step === 'manual') && (
        <div className="space-y-6">
          {step === 'review' && (
            <div 
              className="flex items-center gap-3 p-4 rounded-xl"
              style={{ background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(74, 222, 128, 0.1) 100%)', border: '1px solid rgba(34, 197, 94, 0.3)' }}
            >
              <CheckCircle className="w-5 h-5 flex-shrink-0" style={{ color: 'var(--status-published)' }} />
              <p className="text-sm" style={{ color: 'var(--neutral-dark)' }}>
                Successfully extracted details! Review and edit as needed.
              </p>
            </div>
          )}

          <div className="glass-card rounded-2xl p-6 space-y-5">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Job Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={editedData.title || ''}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                placeholder="e.g., Senior Software Engineer"
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Description <span className="text-red-500">*</span>
              </label>
              <textarea
                value={editedData.description || ''}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                placeholder="Describe the role, responsibilities..."
                rows={6}
                className={`${inputStyle} resize-none`}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>

            {/* Requirements */}
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Requirements
              </label>
              <textarea
                value={editedData.requirements || ''}
                onChange={(e) => handleFieldChange('requirements', e.target.value)}
                placeholder="List qualifications, skills..."
                rows={4}
                className={`${inputStyle} resize-none`}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>

            {/* Location & Work Type */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Location
                </label>
                <input
                  type="text"
                  value={editedData.location || ''}
                  onChange={(e) => handleFieldChange('location', e.target.value)}
                  placeholder="e.g., San Francisco, CA"
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Work Type
                </label>
                <SelectDropdown
                  options={WORK_TYPE_OPTIONS}
                  value={editedData.work_type || ''}
                  onChange={(val) => handleFieldChange('work_type', val || undefined)}
                  placeholder="Select work type..."
                />
              </div>
            </div>

            {/* Salary */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Salary Min
                </label>
                <input
                  type="number"
                  value={editedData.salary_range_min || ''}
                  onChange={(e) => handleFieldChange('salary_range_min', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="50000"
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Salary Max
                </label>
                <input
                  type="number"
                  value={editedData.salary_range_max || ''}
                  onChange={(e) => handleFieldChange('salary_range_max', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="100000"
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Experience */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Experience Min (years)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={editedData.experience_min ?? ''}
                  onChange={(e) => handleFieldChange('experience_min', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="e.g., 3"
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Experience Max (years)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={editedData.experience_max ?? ''}
                  onChange={(e) => handleFieldChange('experience_max', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="e.g., 5"
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Openings */}
            <div className="sm:w-1/2">
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Number of Openings
              </label>
              <input
                type="number"
                value={editedData.openings_count || 1}
                onChange={(e) => handleFieldChange('openings_count', Number(e.target.value) || 1)}
                min={1}
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleReset}
              className="btn-glass flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium"
              style={{ color: 'var(--neutral-dark)' }}
            >
              <RefreshCw className="w-4 h-4" />
              Start Over
            </button>
            <button
              onClick={handleCreateJob}
              disabled={createJob.isPending || !editedData.title || !editedData.description}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-medium text-white disabled:opacity-50 transition-colors hover:opacity-90"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              {createJob.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Create Job'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
