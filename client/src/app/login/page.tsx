'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ROUTES } from '@/constants';
import { useAuthStore } from '@/stores';
import { getEmployerByEmail } from '@/services';
import { getErrorMessage } from '@/lib/api';

/**
 * Login Page - Glassmorphism design
 */
export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, setEmployer } = useAuthStore();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push(ROUTES.DASHBOARD);
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const employer = await getEmployerByEmail(email);
      setEmployer(employer);
      toast.success(`Welcome back, ${employer.name}!`);
      router.push(ROUTES.DASHBOARD);
    } catch (err) {
      const message = getErrorMessage(err);
      if (message.includes('not found')) {
        setError('No account found with this email. Please register first.');
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
        <div className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }} />
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
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        <div 
          className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full opacity-20 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #EC4899 0%, #7C3AED 100%)' }}
        />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href={ROUTES.HOME} className="inline-block">
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
            Enter your email to access your dashboard
          </p>

          {/* Error Message */}
          {error && (
            <div 
              className="mb-6 p-4 rounded-xl text-sm"
              style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#991B1B' }}
            >
              {error}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2"
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
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
            <Link href={ROUTES.REGISTER} className="font-medium hover:underline gradient-text">
              Create one
            </Link>
          </p>
        </div>

        {/* Back to Home */}
        <p className="text-center mt-6">
          <Link href={ROUTES.HOME} className="text-sm transition-colors hover:opacity-70" style={{ color: 'var(--neutral-gray)' }}>
            ← Back to Home
          </Link>
        </p>
      </div>
    </main>
  );
}
