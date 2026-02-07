'use client';

import { ProfileStyleSelect } from '@/components/ui';
import { CANDIDATE_VALIDATION, ROUTES } from '@/constants';
import { getErrorMessage, isApiError } from '@/lib/api';
import { useJobCategories, useRolesByCategory } from '@/lib/hooks/use-candidate';
import { candidateSignup, getCandidateByMobile } from '@/services';
import { useCandidateAuthStore } from '@/stores';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';

/**
 * Candidate Register (Signup) Page - Mobile-based authentication.
 *
 * Design: Same glassmorphism as employer register, adapted for candidate fields.
 * Flow: Mobile + Name (required) + optional basic profile fields.
 * Mobile number is the single source of truth and immutable after creation.
 */
export default function CandidateRegisterPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, setCandidate } = useCandidateAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    mobile: '',
    name: '',
    current_location: '',
    preferred_job_category_id: '',
    preferred_job_role_id: '',
    preferred_job_location: '',
  });

  // Mobile validation state
  const [mobileChecking, setMobileChecking] = useState(false);
  const [mobileError, setMobileError] = useState('');

  // Fetch job categories for dropdown
  const { data: categories = [], isLoading: categoriesLoading } = useJobCategories();

  // Fetch roles for selected category
  const { data: roles = [], isLoading: rolesLoading } = useRolesByCategory(
    formData.preferred_job_category_id || undefined
  );

  // Options for ProfileStyleSelect (scrollable + add custom): real options only, no empty placeholder
  const categoryOptions = categories.map((cat) => ({
    value: cat.id,
    label: cat.name,
    slug: cat.slug,
  }));

  const roleOptions = roles.map((role) => ({
    value: role.id,
    label: role.name,
    slug: role.slug,
  }));

  // Redirect if already authenticated (and profile complete, else complete-profile handles redirect)
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const c = useCandidateAuthStore.getState().candidate;
      if (c?.profile_status === 'complete') router.push(ROUTES.CANDIDATE_DASHBOARD);
      else router.push(ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE);
    }
  }, [isAuthenticated, authLoading, router]);

  // Handle mobile input: digits only, max 10
  const handleMobileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 10);
    setFormData((prev) => ({ ...prev, mobile: value }));
    setMobileError('');
    setError('');
  };

  // Debounced mobile uniqueness check
  const checkMobileUniqueness = useCallback(async (mobile: string) => {
    if (!CANDIDATE_VALIDATION.MOBILE_REGEX.test(mobile)) return;

    setMobileChecking(true);
    try {
      await getCandidateByMobile(mobile);
      // If we get here, mobile already exists
      setMobileError('This mobile number is already registered. Please login instead.');
    } catch {
      // 404 = mobile not found = good to proceed
      setMobileError('');
    } finally {
      setMobileChecking(false);
    }
  }, []);

  // Trigger mobile check after 10 digits entered
  useEffect(() => {
    if (formData.mobile.length === 10 && CANDIDATE_VALIDATION.MOBILE_REGEX.test(formData.mobile)) {
      const timer = setTimeout(() => checkMobileUniqueness(formData.mobile), 300);
      return () => clearTimeout(timer);
    }
  }, [formData.mobile, checkMobileUniqueness]);

  // Reset role when category changes
  useEffect(() => {
    setFormData((prev) => ({ ...prev, preferred_job_role_id: '' }));
  }, [formData.preferred_job_category_id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate mobile
    if (!CANDIDATE_VALIDATION.MOBILE_REGEX.test(formData.mobile)) {
      setError('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    // Validate name
    if (
      formData.name.trim().length < CANDIDATE_VALIDATION.NAME_MIN_LENGTH ||
      formData.name.trim().length > CANDIDATE_VALIDATION.NAME_MAX_LENGTH
    ) {
      setError(`Name must be between ${CANDIDATE_VALIDATION.NAME_MIN_LENGTH} and ${CANDIDATE_VALIDATION.NAME_MAX_LENGTH} characters.`);
      return;
    }

    // Bail if mobile already exists
    if (mobileError) return;

    setIsLoading(true);

    try {
      const response = await candidateSignup({
        mobile: formData.mobile,
        name: formData.name.trim(),
        current_location: formData.current_location.trim() || undefined,
        preferred_job_category_id: formData.preferred_job_category_id || undefined,
        preferred_job_role_id: formData.preferred_job_role_id || undefined,
        preferred_job_location: formData.preferred_job_location.trim() || undefined,
      });

      setCandidate(response.candidate);
      toast.success('Account created successfully! Complete your profile to continue.');
      // Pass signup form data for pre-fill on complete-profile page
      if (typeof window !== 'undefined') {
        sessionStorage.setItem(
          'aiviue_complete_profile_prefill',
          JSON.stringify({
            name: formData.name.trim(),
            current_location: formData.current_location.trim(),
            preferred_job_category_id: formData.preferred_job_category_id,
            preferred_job_role_id: formData.preferred_job_role_id,
            preferred_job_location: formData.preferred_job_location.trim(),
          })
        );
      }
      router.push(ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE);
    } catch (err) {
      if (isApiError(err, 'MOBILE_ALREADY_EXISTS') || isApiError(err, 'CONFLICT')) {
        setMobileError('This mobile number is already registered. Please login instead.');
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle =
    'w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2';

  // Show loading while checking auth state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div
          className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin"
          style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }}
        />
      </div>
    );
  }

  // Don't render form if already authenticated (will redirect)
  if (isAuthenticated) {
    return null;
  }

  return (
    <main className="min-h-screen gradient-bg flex items-center justify-center p-4 py-8 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-30 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #7C3AED 100%)' }}
        />
        <div
          className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full opacity-20 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        <div
          className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full opacity-15 blur-3xl transform -translate-x-1/2 -translate-y-1/2"
          style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #7C3AED 100%)' }}
        />
      </div>

      <div className="w-full max-w-lg relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href={ROUTES.CANDIDATE_HOME} className="inline-block">
            <Image
              src="/aiviue-logo.png"
              alt="AIVIUE"
              width={240}
              height={80}
              className="h-20 sm:h-24 w-auto mx-auto"
              priority
            />
          </Link>
          
        </div>

        {/* Register Card */}
        <div className="glass-card rounded-3xl p-5 sm:p-8">
          <h1 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Create Your Account
          </h1>
          <p className="text-sm text-center mb-6 text-slate-500">
            Build your resume and discover matching jobs
          </p>

          {/* Error Message */}
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

          {/* Register Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Mobile & Name Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Mobile Number */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Mobile Number <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <span
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-medium"
                    style={{ color: 'var(--neutral-gray)' }}
                  >
                    +91
                  </span>
                  <input
                    type="tel"
                    inputMode="numeric"
                    value={formData.mobile}
                    onChange={handleMobileChange}
                    placeholder="9876543210"
                    required
                    autoFocus
                    maxLength={10}
                    className="w-full pl-14 pr-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2"
                    style={{
                      borderColor: mobileError ? 'rgba(239, 68, 68, 0.5)' : 'var(--neutral-border)',
                      '--tw-ring-color': 'var(--primary)',
                    } as React.CSSProperties}
                  />
                  {mobileChecking && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <div
                        className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin"
                        style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }}
                      />
                    </div>
                  )}
                </div>
                {mobileError && (
                  <p className="mt-1.5 text-xs text-red-600">{mobileError}</p>
                )}
                {formData.mobile.length > 0 && formData.mobile.length < 10 && !mobileError && (
                  <p className="mt-1.5 text-xs" style={{ color: 'var(--neutral-muted)' }}>
                    {10 - formData.mobile.length} more digit{10 - formData.mobile.length !== 1 ? 's' : ''} needed
                  </p>
                )}
              </div>

              {/* Name */}
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
                  minLength={CANDIDATE_VALIDATION.NAME_MIN_LENGTH}
                  maxLength={CANDIDATE_VALIDATION.NAME_MAX_LENGTH}
                  className={inputStyle}
                  style={{
                    borderColor: 'var(--neutral-border)',
                    '--tw-ring-color': 'var(--primary)',
                  } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Location Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Current Location
                </label>
                <input
                  name="current_location"
                  type="text"
                  value={formData.current_location}
                  onChange={handleChange}
                  placeholder="e.g. Mumbai, Delhi"
                  className={inputStyle}
                  style={{
                    borderColor: 'var(--neutral-border)',
                    '--tw-ring-color': 'var(--primary)',
                  } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Preferred Job Location
                </label>
                <input
                  name="preferred_job_location"
                  type="text"
                  value={formData.preferred_job_location}
                  onChange={handleChange}
                  placeholder="e.g. Bangalore, Pune"
                  className={inputStyle}
                  style={{
                    borderColor: 'var(--neutral-border)',
                    '--tw-ring-color': 'var(--primary)',
                  } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Job Category & Role – scrollable dropdowns with "Or type your own" */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ProfileStyleSelect
                label="Preferred Job Category"
                options={categoryOptions}
                value={formData.preferred_job_category_id}
                onChange={(val) =>
                  setFormData((prev) => ({ ...prev, preferred_job_category_id: val }))
                }
                placeholder={categoriesLoading ? 'Loading categories...' : 'Select a job category...'}
                isLoading={categoriesLoading}
                allowCustom
                customPlaceholder="Or type your category"
              />
              <ProfileStyleSelect
                label="Preferred Job Role"
                options={roleOptions}
                value={formData.preferred_job_role_id}
                onChange={(val) =>
                  setFormData((prev) => ({ ...prev, preferred_job_role_id: val }))
                }
                placeholder={
                  rolesLoading
                    ? 'Loading roles...'
                    : formData.preferred_job_category_id
                      ? 'Select a role...'
                      : 'Select category first...'
                }
                disabled={!formData.preferred_job_category_id}
                isLoading={rolesLoading}
                allowCustom
                customPlaceholder="Or type your role (e.g. Backend Developer)"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !!mobileError || mobileChecking}
              className="w-full py-3.5 rounded-xl text-white font-semibold disabled:opacity-50 flex items-center justify-center gap-2 mt-6 transition-colors hover:opacity-90"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className="text-center text-sm mt-6" style={{ color: 'var(--neutral-gray)' }}>
            Already have an account?{' '}
            <Link href={ROUTES.CANDIDATE_LOGIN} className="font-medium hover:underline gradient-text">
              Sign in
            </Link>
          </p>
        </div>

        {/* Back to Candidate Home */}
        <p className="text-center mt-6">
          <Link
            href={ROUTES.CANDIDATE_HOME}
            className="text-sm transition-colors hover:opacity-70"
            style={{ color: 'var(--neutral-gray)' }}
          >
            ← Back to Candidate Home
          </Link>
        </p>
      </div>
    </main>
  );
}
