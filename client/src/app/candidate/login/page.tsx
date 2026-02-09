'use client';

import { CANDIDATE_VALIDATION, ROUTES } from '@/constants';
import { getErrorMessage } from '@/lib/api';
import { useCandidateAuthStore } from '@/stores';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

/**
 * Candidate Login Page - Mobile number based authentication.
 *
 * Design: Same glassmorphism as employer login, adapted for mobile input.
 * Auth: Mobile number is the single source of truth (no password, no OTP for MVP).
 */
export default function CandidateLoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, login } = useCandidateAuthStore();
  const [mobile, setMobile] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already authenticated (to dashboard or complete-profile if basic)
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const c = useCandidateAuthStore.getState().candidate;
      if (c?.profile_status === 'complete') router.push(ROUTES.CANDIDATE_DASHBOARD);
      else router.push(ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE);
    }
  }, [isAuthenticated, authLoading, router]);

  const handleMobileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Only allow digits, max 10 characters
    const value = e.target.value.replace(/\D/g, '').slice(0, 10);
    setMobile(value);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate mobile number
    if (!CANDIDATE_VALIDATION.MOBILE_REGEX.test(mobile)) {
      setError('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    setIsLoading(true);

    try {
      await login(mobile);
      const candidate = useCandidateAuthStore.getState().candidate;
      if (candidate) {
        toast.success(`Welcome back, ${candidate.name}!`);
        if (candidate.profile_status === 'complete') router.push(ROUTES.CANDIDATE_DASHBOARD);
        else router.push(ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE);
      }
    } catch (err) {
      const message = getErrorMessage(err);
      if (message.includes('not found') || message.includes('Not Found')) {
        setError('No account found with this mobile number. Please sign up first.');
      } else {
        setError(message);
      }
    } finally {
      setIsLoading(false);
    }
  };

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

  // Don't render login form if already authenticated (will redirect)
  if (isAuthenticated) {
    return null;
  }

  return (
    <main className="min-h-screen gradient-bg flex items-center justify-center p-4 relative overflow-hidden">
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
      </div>

      <div className="w-full max-w-md relative z-10">
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

        {/* Login Card */}
        <div className="glass-card rounded-3xl p-6 sm:p-8">
          <h1 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Welcome Back
          </h1>
          <p className="text-sm text-center mb-6" style={{ color: 'var(--neutral-gray)' }}>
            Enter your mobile number to access your dashboard
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

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Mobile Number
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
                  value={mobile}
                  onChange={handleMobileChange}
                  placeholder="9876543210"
                  required
                  autoFocus
                  maxLength={10}
                  className="w-full pl-14 pr-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2"
                  style={{
                    borderColor: error ? 'rgba(239, 68, 68, 0.5)' : 'var(--neutral-border)',
                    '--tw-ring-color': 'var(--primary)',
                  } as React.CSSProperties}
                />
              </div>
              {mobile.length > 0 && mobile.length < 10 && (
                <p className="mt-1.5 text-xs" style={{ color: 'var(--neutral-muted)' }}>
                  {10 - mobile.length} more digit{10 - mobile.length !== 1 ? 's' : ''} needed
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || mobile.length !== 10}
              className="w-full py-3.5 rounded-xl text-white font-semibold disabled:opacity-50 flex items-center justify-center gap-2 transition-colors hover:opacity-90"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Signing in...
                </>
              ) : (
                'Continue'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 h-px" style={{ backgroundColor: 'var(--neutral-border)' }} />
            <span className="text-xs" style={{ color: 'var(--neutral-gray)' }}>or</span>
            <div className="flex-1 h-px" style={{ backgroundColor: 'var(--neutral-border)' }} />
          </div>

          {/* Register Link */}
          <p className="text-center text-sm" style={{ color: 'var(--neutral-gray)' }}>
            Don&apos;t have an account?{' '}
            <Link href={ROUTES.CANDIDATE_REGISTER} className="font-medium hover:underline gradient-text">
              Create one
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
