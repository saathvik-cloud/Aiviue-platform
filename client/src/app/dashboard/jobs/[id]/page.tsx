'use client';

import { ROUTES, WORK_TYPES } from '@/constants';
import { useCloseJob, useJob, usePublishJob } from '@/lib/hooks';
import { capitalize, formatDate, formatSalaryRange } from '@/lib/utils';
import {
  AlertCircle,
  ArrowLeft,
  Briefcase,
  Building,
  Calendar,
  CheckCircle,
  Clock,
  DollarSign,
  Edit,
  Globe,
  Loader2,
  MapPin,
  Play,
  Send,
  Users,
  Video,
  XCircle
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';
import { toast } from 'sonner';

/**
 * Job Details Page - Premium Glassmorphism Design
 * Layout: Left column for video, Right column for details
 */
export default function JobDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;

  const { data: job, isLoading, refetch } = useJob(jobId);
  const publishMutation = usePublishJob();
  const closeMutation = useCloseJob();

  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [closeReason, setCloseReason] = useState('');

  const handlePublish = async () => {
    if (!job) return;

    try {
      await publishMutation.mutateAsync({
        id: job.id,
        data: { version: job.version },
      });
      toast.success('Job published successfully! Event sent to Screening Agent.');
      setShowPublishModal(false);
      refetch();
    } catch {
      toast.error('Failed to publish job');
    }
  };

  const handleClose = async () => {
    if (!job) return;

    try {
      await closeMutation.mutateAsync({
        id: job.id,
        data: { version: job.version, reason: closeReason || undefined },
      });
      toast.success('Job closed successfully');
      setShowCloseModal(false);
      setCloseReason('');
      refetch();
    } catch {
      toast.error('Failed to close job');
    }
  };

  // Section themes for Job Description
  interface DescriptionSection {
    title: string;
    color: string;
    bullets: string[];
  }

  // Smart parsing - breaks description into themed sections
  const parseIntoSections = (text: string | undefined | null): DescriptionSection[] => {
    if (!text) return [];

    // Split into paragraphs/sentences
    const paragraphs = text
      .split(/[\n\r]+/)
      .map(p => p.trim())
      .filter(p => p.length > 0);

    // Theme colors
    const themes = [
      { title: '🎯 About This Opportunity', color: '#7C3AED' },
      { title: '💼 Your Role', color: '#2563EB' },
      { title: '✨ What You\'ll Do', color: '#0891B2' },
      { title: '🤝 Why Join Us', color: '#059669' },
    ];

    // If very short, just return as single section
    if (paragraphs.length <= 1) {
      return [{
        title: themes[0].title,
        color: themes[0].color,
        bullets: paragraphs,
      }];
    }

    // Distribute paragraphs into sections
    const sections: DescriptionSection[] = [];
    const itemsPerSection = Math.ceil(paragraphs.length / themes.length);

    for (let i = 0; i < themes.length && i * itemsPerSection < paragraphs.length; i++) {
      const start = i * itemsPerSection;
      const end = Math.min(start + itemsPerSection, paragraphs.length);
      const sectionBullets = paragraphs.slice(start, end);

      if (sectionBullets.length > 0) {
        // Break long paragraphs into smaller bullet points
        const splitBullets: string[] = [];
        sectionBullets.forEach(para => {
          // Split by sentences if paragraph is too long
          if (para.length > 200) {
            const sentences = para.match(/[^.!?]+[.!?]+/g) || [para];
            splitBullets.push(...sentences.map(s => s.trim()).filter(s => s.length > 10));
          } else {
            splitBullets.push(para);
          }
        });

        sections.push({
          title: themes[i].title,
          color: themes[i].color,
          bullets: splitBullets.slice(0, 4), // Max 4 bullets per section
        });
      }
    }

    return sections;
  };

  // Parse requirements into simple bullet points
  const parseIntoBullets = (text: string | undefined | null): string[] => {
    if (!text) return [];
    return text
      .split(/[\n\r]+/)
      .map(line => line.replace(/^[-•*\d.)\s]+/, '').trim())
      .filter(line => line.length > 0);
  };

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

  const workTypeLabel = WORK_TYPES.find(t => t.value === job.work_type)?.label || job.work_type;
  const descriptionSections = parseIntoSections(job.description);
  const requirementsBullets = parseIntoBullets(job.requirements);

  return (
    <div className="space-y-4">
      {/* Compact Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-4">
          <Link href={ROUTES.JOBS} className="p-2 rounded-xl hover:bg-white/50 transition-colors" style={{ color: 'var(--neutral-gray)' }}>
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className={`status-badge status-${job.status}`}>
                {capitalize(job.status)}
              </span>
              {job.is_published && (
                <span className="text-xs flex items-center gap-1" style={{ color: 'var(--neutral-gray)' }}>
                  <Clock className="w-3 h-3" />
                  {formatDate(job.published_at!)}
                </span>
              )}
            </div>
            <h1 className="text-xl sm:text-2xl font-bold mt-1" style={{ color: 'var(--neutral-dark)' }}>
              {job.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href={ROUTES.JOB_EDIT(job.id)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
            style={{
              background: 'rgba(255,255,255,0.7)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.3)',
              color: 'var(--neutral-dark)'
            }}
          >
            <Edit className="w-4 h-4" />
            Edit
          </Link>

          {job.status === 'draft' && (
            <button
              onClick={() => setShowPublishModal(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-sm font-medium transition-all shadow-lg hover:shadow-xl hover:scale-105"
              style={{ background: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)' }}
            >
              <Send className="w-4 h-4" />
              Publish
            </button>
          )}

          {job.status === 'published' && (
            <button
              onClick={() => setShowCloseModal(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--status-closed)' }}
            >
              <XCircle className="w-4 h-4" />
              Close
            </button>
          )}
        </div>
      </div>

      {/* Main Content Grid - Left: Video, Right: Details */}
      <div className="grid lg:grid-cols-6 gap-4">

        {/* Left Column - Video Card (3 cols) */}
        <div className="lg:col-span-3">
          <div
            className="rounded-2xl p-6 h-full min-h-[400px] flex flex-col items-center justify-center relative overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
              backdropFilter: 'blur(20px)',
              border: '2px solid rgba(255,255,255,0.4)',
              boxShadow: '0 8px 32px rgba(124, 58, 237, 0.1)',
            }}
          >
            {/* Decorative circles */}
            <div className="absolute top-4 right-4 w-32 h-32 rounded-full opacity-20 blur-2xl" style={{ background: 'var(--gradient-primary)' }} />
            <div className="absolute bottom-4 left-4 w-24 h-24 rounded-full opacity-10 blur-xl" style={{ background: 'var(--gradient-accent)' }} />

            <div className="relative z-10 text-center">
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{
                  background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.15) 100%)',
                  border: '2px solid rgba(124, 58, 237, 0.2)',
                }}
              >
                <Video className="w-10 h-10" style={{ color: 'var(--primary)' }} />
              </div>
              <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--neutral-dark)' }}>
                JOB-VIDEO
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
                Job video will appear here..
              </p>
              <button
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-medium mx-auto transition-all hover:scale-105"
                style={{ background: 'var(--gradient-primary)', boxShadow: '0 4px 15px rgba(124, 58, 237, 0.3)' }}
              >
                <Play className="w-4 h-4" />
                Coming Soon
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Details (3 cols) */}
        <div className="lg:col-span-3 space-y-4">

          {/* Info Tiles Grid - 4 cards */}
          <div className="grid grid-cols-2 gap-3">
            {/* Location Tile */}
            <div
              className="rounded-xl p-4 relative overflow-hidden group transition-all hover:scale-[1.02]"
              style={{
                background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(168, 85, 247, 0.08) 100%)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(124, 58, 237, 0.15)',
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)' }}
                >
                  <MapPin className="w-5 h-5" style={{ color: '#7C3AED' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#7C3AED' }}>Location</p>
                  <p className="text-sm font-semibold truncate mt-0.5" style={{ color: 'var(--neutral-dark)' }}>
                    {[job.city, job.state, job.country].filter(Boolean).join(', ') || job.location || 'Not specified'}
                  </p>
                </div>
              </div>
            </div>

            {/* Salary Tile */}
            <div
              className="rounded-xl p-4 relative overflow-hidden group transition-all hover:scale-[1.02]"
              style={{
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(74, 222, 128, 0.08) 100%)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(34, 197, 94, 0.15)',
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(74, 222, 128, 0.2) 100%)' }}
                >
                  <DollarSign className="w-5 h-5" style={{ color: '#22C55E' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#22C55E' }}>Salary</p>
                  <p className="text-sm font-semibold truncate mt-0.5" style={{ color: 'var(--neutral-dark)' }}>
                    {formatSalaryRange(job.salary_range_min, job.salary_range_max, job.currency) || 'Not specified'}
                  </p>
                </div>
              </div>
            </div>

            {/* Experience Tile */}
            <div
              className="rounded-xl p-4 relative overflow-hidden group transition-all hover:scale-[1.02]"
              style={{
                background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(251, 146, 60, 0.08) 100%)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(249, 115, 22, 0.15)',
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(251, 146, 60, 0.2) 100%)' }}
                >
                  <Briefcase className="w-5 h-5" style={{ color: '#F97316' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#F97316' }}>Experience</p>
                  <p className="text-sm font-semibold mt-0.5" style={{ color: 'var(--neutral-dark)' }}>
                    {job.experience_range || `${job.experience_min || 0}-${job.experience_max || 0} years`}
                  </p>
                </div>
              </div>
            </div>

            {/* Work Type Tile */}
            <div
              className="rounded-xl p-4 relative overflow-hidden group transition-all hover:scale-[1.02]"
              style={{
                background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(244, 114, 182, 0.08) 100%)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(236, 72, 153, 0.15)',
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(244, 114, 182, 0.2) 100%)' }}
                >
                  <Globe className="w-5 h-5" style={{ color: '#EC4899' }} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wide" style={{ color: '#EC4899' }}>Work Type</p>
                  <p className="text-sm font-semibold mt-0.5" style={{ color: 'var(--neutral-dark)' }}>
                    {workTypeLabel}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Job Description Card - Glassmorphic Stone Gradient */}
          <div
            className="rounded-2xl p-5 relative overflow-hidden"
            style={{
              background: 'linear-gradient(145deg, rgba(245, 243, 240, 0.95) 0%, rgba(231, 225, 217, 0.85) 50%, rgba(214, 205, 193, 0.75) 100%)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.6)',
              boxShadow: '0 8px 32px rgba(120, 100, 80, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
            }}
          >
            {/* Decorative subtle gradient overlay */}
            <div
              className="absolute top-0 right-0 w-40 h-40 opacity-20 blur-3xl"
              style={{ background: 'radial-gradient(circle, rgba(180, 160, 140, 0.3) 0%, transparent 70%)' }}
            />

            <div className="flex items-center gap-2 mb-5">
              <div
                className="w-2 h-6 rounded-full"
                style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
              />
              <h2 className="text-base font-bold" style={{ color: 'var(--neutral-dark)' }}>
                Job Description
              </h2>
            </div>

            {/* Sectioned Content */}
            <div className="space-y-5">
              {descriptionSections.length > 0 ? (
                descriptionSections.map((section, sectionIndex) => (
                  <div key={sectionIndex} className="relative">
                    {/* Section Header */}
                    <h3
                      className="text-sm font-semibold mb-3 flex items-center gap-2"
                      style={{ color: section.color }}
                    >
                      {section.title}
                    </h3>

                    {/* Section Bullets */}
                    <div className="space-y-2 ml-1">
                      {section.bullets.map((bullet: string, bulletIndex: number) => (
                        <div key={bulletIndex} className="flex items-start gap-2.5">
                          <span
                            className="w-1.5 h-1.5 rounded-full mt-2 shrink-0"
                            style={{ backgroundColor: section.color }}
                          />
                          <span
                            className="text-sm leading-relaxed"
                            style={{ color: '#4A4A4A' }}
                          >
                            {bullet}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                  No description provided.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Requirements Card - Full Width with Stone Gradient */}
      <div
        className="rounded-2xl p-5 relative overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(240, 245, 243, 0.95) 0%, rgba(220, 235, 230, 0.85) 50%, rgba(195, 220, 210, 0.75) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(20, 184, 166, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
        }}
      >
        <div className="flex items-center gap-2 mb-4">
          <div
            className="w-2 h-6 rounded-full"
            style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #2DD4BF 100%)' }}
          />
          <h2 className="text-base font-bold" style={{ color: 'var(--neutral-dark)' }}>
            Requirements
          </h2>
        </div>
        <div className="grid md:grid-cols-2 gap-x-8 gap-y-2.5 text-sm leading-relaxed">
          {requirementsBullets.length > 0 ? (
            requirementsBullets.map((bullet: string, index: number) => (
              <div key={index} className="flex items-start gap-2.5">
                <CheckCircle
                  className="w-4 h-4 mt-0.5 shrink-0"
                  style={{ color: '#14B8A6' }}
                />
                <span style={{ color: '#4A4A4A' }}>{bullet}</span>
              </div>
            ))
          ) : (
            <p style={{ color: 'var(--neutral-gray)' }}>No requirements specified.</p>
          )}
        </div>
      </div>

      {/* Additional Info Card with Stone Gradient */}
      <div
        className="rounded-2xl p-5 relative overflow-hidden"
        style={{
          background: 'linear-gradient(145deg, rgba(245, 243, 250, 0.95) 0%, rgba(235, 230, 245, 0.85) 50%, rgba(220, 215, 235, 0.75) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 8px 32px rgba(99, 102, 241, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
        }}
      >
        <div className="flex items-center gap-2 mb-4">
          <div
            className="w-2 h-6 rounded-full"
            style={{ background: 'linear-gradient(135deg, #6366F1 0%, #818CF8 100%)' }}
          />
          <h2 className="text-base font-bold" style={{ color: 'var(--neutral-dark)' }}>
            Additional Information
          </h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(99, 102, 241, 0.1)' }}
            >
              <Calendar className="w-4 h-4" style={{ color: '#6366F1' }} />
            </div>
            <div>
              <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Created</p>
              <p className="text-xs font-medium" style={{ color: 'var(--neutral-dark)' }}>{formatDate(job.created_at)}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(99, 102, 241, 0.1)' }}
            >
              <Clock className="w-4 h-4" style={{ color: '#6366F1' }} />
            </div>
            <div>
              <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Updated</p>
              <p className="text-xs font-medium" style={{ color: 'var(--neutral-dark)' }}>{formatDate(job.updated_at)}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: 'rgba(20, 184, 166, 0.1)' }}
            >
              <Users className="w-4 h-4" style={{ color: '#14B8A6' }} />
            </div>
            <div>
              <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Openings</p>
              <p className="text-xs font-medium" style={{ color: 'var(--neutral-dark)' }}>{job.openings_count}</p>
            </div>
          </div>
          {job.shift_preferences && Object.keys(job.shift_preferences).length > 0 && (
            <div className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center"
                style={{ background: 'rgba(249, 115, 22, 0.1)' }}
              >
                <Building className="w-4 h-4" style={{ color: '#F97316' }} />
              </div>
              <div>
                <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>Shift</p>
                <p className="text-xs font-medium capitalize" style={{ color: 'var(--neutral-dark)' }}>
                  {typeof job.shift_preferences === 'string'
                    ? job.shift_preferences
                    : Object.keys(job.shift_preferences).join(', ')}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Publish Modal */}
      {showPublishModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div
            className="rounded-3xl p-6 w-full max-w-md"
            style={{
              background: 'rgba(255,255,255,0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.5)',
              boxShadow: '0 25px 50px rgba(0,0,0,0.15)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-center">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(74, 222, 128, 0.1) 100%)' }}
              >
                <Send className="w-8 h-8" style={{ color: 'var(--status-published)' }} />
              </div>
              <h3 className="text-xl font-semibold" style={{ color: 'var(--neutral-dark)' }}>Publish Job?</h3>
              <p className="text-sm mt-2" style={{ color: 'var(--neutral-gray)' }}>
                This will make the job visible and send an event to the Screening Agent.
              </p>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowPublishModal(false)}
                className="flex-1 px-4 py-3 rounded-xl text-sm font-medium transition-colors"
                style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--neutral-dark)' }}
              >
                Cancel
              </button>
              <button
                onClick={handlePublish}
                disabled={publishMutation.isPending}
                className="flex-1 px-4 py-3 rounded-xl text-white text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg"
                style={{ background: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)' }}
              >
                {publishMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Publish
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Close Modal */}
      {showCloseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div
            className="rounded-3xl p-6 w-full max-w-md"
            style={{
              background: 'rgba(255,255,255,0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.5)',
              boxShadow: '0 25px 50px rgba(0,0,0,0.15)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-center">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(248, 113, 113, 0.1) 100%)' }}
              >
                <XCircle className="w-8 h-8" style={{ color: 'var(--status-closed)' }} />
              </div>
              <h3 className="text-xl font-semibold" style={{ color: 'var(--neutral-dark)' }}>Close Job?</h3>
              <p className="text-sm mt-2" style={{ color: 'var(--neutral-gray)' }}>
                This will mark the job as closed. You can optionally provide a reason.
              </p>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Reason (optional)
              </label>
              <input
                type="text"
                value={closeReason}
                onChange={(e) => setCloseReason(e.target.value)}
                placeholder="e.g., Position filled"
                className="w-full px-4 py-3 rounded-xl border text-sm outline-none bg-white/50 focus:bg-white focus:ring-2 transition-all"
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCloseModal(false)}
                className="flex-1 px-4 py-3 rounded-xl text-sm font-medium transition-colors"
                style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--neutral-dark)' }}
              >
                Cancel
              </button>
              <button
                onClick={handleClose}
                disabled={closeMutation.isPending}
                className="flex-1 px-4 py-3 rounded-xl text-white text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                style={{ backgroundColor: 'var(--status-closed)' }}
              >
                {closeMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <XCircle className="w-4 h-4" />
                    Close Job
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
