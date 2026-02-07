'use client';

/**
 * Complete Profile Page - Mandatory step after signup (Option B).
 *
 * User must fill: name, current_location, preferred_job_category_id,
 * preferred_job_role_id, preferred_job_location. Data can be pre-filled
 * from register form via sessionStorage. Anytime after, profile can be
 * updated via Profile in the header dropdown.
 */

import { ProfileStyleSelect } from '@/components/ui';
import { ROUTES } from '@/constants';
import { useJobCategories, useRolesByCategory } from '@/lib/hooks';
import { createBasicProfile } from '@/services';
import { useCandidateAuthStore } from '@/stores';
import { getErrorMessage } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

const PREFILL_KEY = 'aiviue_complete_profile_prefill';

export default function CompleteProfilePage() {
  const router = useRouter();
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const setCandidate = useCandidateAuthStore((state) => state.setCandidate);

  const [formData, setFormData] = useState({
    name: '',
    current_location: '',
    preferred_job_category_id: '',
    preferred_job_role_id: '',
    preferred_job_location: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { data: categories = [], isLoading: categoriesLoading, isError: categoriesError } = useJobCategories();
  const { data: roles = [], isLoading: rolesLoading } = useRolesByCategory(
    formData.preferred_job_category_id || undefined
  );

  const categoryOptions = categories.map((c) => ({
    value: c.id,
    label: c.name,
    slug: c.slug,
  }));
  const roleOptions = roles.map((r) => ({
    value: r.id,
    label: r.name,
    slug: r.slug,
  }));

  // Pre-fill from sessionStorage (set by register page) or from candidate
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const raw = sessionStorage.getItem(PREFILL_KEY);
      if (raw) {
        const prefill = JSON.parse(raw) as Record<string, string>;
        setFormData((prev) => ({
          ...prev,
          name: prefill.name ?? prev.name ?? candidate?.name ?? '',
          current_location: prefill.current_location ?? prev.current_location ?? candidate?.current_location ?? '',
          preferred_job_category_id: prefill.preferred_job_category_id ?? prev.preferred_job_category_id ?? candidate?.preferred_job_category_id ?? '',
          preferred_job_role_id: prefill.preferred_job_role_id ?? prev.preferred_job_role_id ?? candidate?.preferred_job_role_id ?? '',
          preferred_job_location: prefill.preferred_job_location ?? prev.preferred_job_location ?? candidate?.preferred_job_location ?? '',
        }));
      } else if (candidate) {
        setFormData((prev) => ({
          ...prev,
          name: candidate.name ?? prev.name,
          current_location: candidate.current_location ?? prev.current_location,
          preferred_job_category_id: candidate.preferred_job_category_id ?? prev.preferred_job_category_id,
          preferred_job_role_id: candidate.preferred_job_role_id ?? prev.preferred_job_role_id,
          preferred_job_location: candidate.preferred_job_location ?? prev.preferred_job_location,
        }));
      }
    } catch {
      if (candidate) {
        setFormData((prev) => ({
          ...prev,
          name: candidate.name ?? prev.name,
          current_location: candidate.current_location ?? prev.current_location,
          preferred_job_category_id: candidate.preferred_job_category_id ?? prev.preferred_job_category_id,
          preferred_job_role_id: candidate.preferred_job_role_id ?? prev.preferred_job_role_id,
          preferred_job_location: candidate.preferred_job_location ?? prev.preferred_job_location,
        }));
      }
    }
  }, [candidate?.id]);

  // If no candidate or already complete, redirect
  useEffect(() => {
    if (!candidate) {
      router.replace(ROUTES.CANDIDATE_LOGIN);
      return;
    }
    if (candidate.profile_status === 'complete') {
      router.replace(ROUTES.CANDIDATE_DASHBOARD);
    }
  }, [candidate, router]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!candidate?.id) return;
      setError('');
      const name = formData.name.trim();
      const current_location = formData.current_location.trim();
      const preferred_job_location = formData.preferred_job_location.trim();
      if (!name || !current_location || !formData.preferred_job_category_id || !formData.preferred_job_role_id || !preferred_job_location) {
        setError('All fields are required.');
        return;
      }
      setIsLoading(true);
      try {
        const updated = await createBasicProfile(candidate.id, {
          name,
          current_location,
          preferred_job_category_id: formData.preferred_job_category_id,
          preferred_job_role_id: formData.preferred_job_role_id,
          preferred_job_location,
        });
        setCandidate(updated);
        if (typeof window !== 'undefined') sessionStorage.removeItem(PREFILL_KEY);
        toast.success('Profile complete! Welcome to your dashboard.');
        router.replace(ROUTES.CANDIDATE_DASHBOARD);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    },
    [candidate?.id, formData, setCandidate, router]
  );

  if (!candidate || candidate.profile_status === 'complete') {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  const inputStyle =
    'w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2';

  return (
    <div className="max-w-xl mx-auto">
      <div className="glass-card rounded-2xl p-6 sm:p-8">
        <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--neutral-dark)' }}>
          Complete your profile
        </h1>
        <p className="text-sm mb-6" style={{ color: 'var(--neutral-gray)' }}>
          Tell us a bit more so we can recommend the right jobs.
        </p>

        {error && (
          <div
            className="mb-6 p-4 rounded-xl text-sm"
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#991B1B',
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              name="name"
              type="text"
              value={formData.name}
              onChange={handleChange}
              placeholder="Your full name"
              required
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Current Location <span className="text-red-500">*</span>
            </label>
            <input
              name="current_location"
              type="text"
              value={formData.current_location}
              onChange={handleChange}
              placeholder="e.g. Mumbai, Delhi"
              required
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>

          <div>
            {categoriesError && (
              <p className="text-sm mb-2" style={{ color: '#b91c1c' }}>
                Could not load categories. Check that the backend is running and try again.
              </p>
            )}
            <ProfileStyleSelect
              label="Preferred Job Category *"
              options={categoryOptions}
              value={formData.preferred_job_category_id}
              onChange={(v) => setFormData((prev) => ({ ...prev, preferred_job_category_id: v, preferred_job_role_id: '' }))}
              placeholder={categoriesLoading ? 'Loading...' : 'Select a job category'}
              isLoading={categoriesLoading}
              allowCustom
              customPlaceholder="Or type your category"
            />
          </div>

          <div>
            <ProfileStyleSelect
              label="Preferred Job Role *"
              options={roleOptions}
              value={formData.preferred_job_role_id}
              onChange={(v) => setFormData((prev) => ({ ...prev, preferred_job_role_id: v }))}
              placeholder={rolesLoading ? 'Loading...' : formData.preferred_job_category_id ? 'Select role' : 'Select category first'}
              disabled={!formData.preferred_job_category_id}
              isLoading={rolesLoading}
              allowCustom
              customPlaceholder="Or type your role (e.g. Backend Developer)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Preferred Job Location <span className="text-red-500">*</span>
            </label>
            <input
              name="preferred_job_location"
              type="text"
              value={formData.preferred_job_location}
              onChange={handleChange}
              placeholder="e.g. Bangalore, Pune"
              required
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 rounded-xl text-white font-semibold disabled:opacity-50 flex items-center justify-center gap-2 mt-6"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            {isLoading ? (
              <>
                <span className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                Saving...
              </>
            ) : (
              'Continue to Dashboard'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
