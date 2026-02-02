'use client';

import { SelectDropdown } from '@/components';
import { ROUTES } from '@/constants';
import { getErrorMessage } from '@/lib/api';
import { createEmployer } from '@/services';
import { useAuthStore } from '@/stores';
import { Briefcase, Building, Building2, Landmark, Users } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';

// Company size options with icons
const COMPANY_SIZE_OPTIONS = [
  { value: '', label: 'Select company size...' },
  { value: 'startup', label: '1-10 employees (Startup)', icon: <Users className="w-4 h-4" style={{ color: 'var(--secondary-teal)' }} /> },
  { value: 'small', label: '11-50 employees (Small)', icon: <Building className="w-4 h-4" style={{ color: 'var(--primary)' }} /> },
  { value: 'medium', label: '51-200 employees (Medium)', icon: <Briefcase className="w-4 h-4" style={{ color: 'var(--accent)' }} /> },
  { value: 'large', label: '201-1000 employees (Large)', icon: <Building2 className="w-4 h-4" style={{ color: 'var(--status-published)' }} /> },
  { value: 'enterprise', label: '1000+ employees (Enterprise)', icon: <Landmark className="w-4 h-4" style={{ color: 'var(--status-pending)' }} /> },
];

/**
 * Register Page - Glassmorphism design with custom dropdown
 */
export default function RegisterPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, setEmployer } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company_name: '',
    company_size: '',
    industry: '',
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push(ROUTES.DASHBOARD);
    }
  }, [isAuthenticated, authLoading, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const employer = await createEmployer({
        name: formData.name,
        email: formData.email,
        phone: formData.phone || undefined,
        company_name: formData.company_name,
        company_size: formData.company_size || undefined,
        industry: formData.industry || undefined,
      });

      setEmployer(employer);
      toast.success('Account created successfully!');
      router.push(ROUTES.DASHBOARD);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle = "w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2";

  // Show loading while checking auth state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  // Don't render register form if already authenticated (will redirect)
  if (isAuthenticated) {
    return null;
  }

  return (
    <main className="min-h-screen gradient-bg flex items-center justify-center p-4 py-8 relative overflow-hidden">
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
        <div
          className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full opacity-15 blur-3xl transform -translate-x-1/2 -translate-y-1/2"
          style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #7C3AED 100%)' }}
        />
      </div>

      <div className="w-full max-w-lg relative z-10">
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

        {/* Register Card */}
        <div className="glass-card rounded-3xl p-5 sm:p-8">
          <h1 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--neutral-dark)' }}>
            Create Your Account
          </h1>
          <p className="text-sm text-center mb-6 text-slate-500" >
            Start hiring smarter with AIVIUE
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

          {/* Register Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name & Email Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Your Name <span className="text-red-500">*</span>
                </label>
                <input
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="John Doe"
                  required
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Work Email <span className="text-red-500">*</span>
                </label>
                <input
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@company.com"
                  required
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Phone & Company Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Phone Number
                </label>
                <input
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="+1-234-567-8900"
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Company Name <span className="text-red-500">*</span>
                </label>
                <input
                  name="company_name"
                  type="text"
                  value={formData.company_name}
                  onChange={handleChange}
                  placeholder="Acme Inc."
                  required
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Company Size & Industry Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Company Size
                </label>
                <SelectDropdown
                  options={COMPANY_SIZE_OPTIONS}
                  value={formData.company_size}
                  onChange={(val) => setFormData(prev => ({ ...prev, company_size: val }))}
                  placeholder="Select company size..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                  Industry
                </label>
                <input
                  name="industry"
                  type="text"
                  value={formData.industry}
                  onChange={handleChange}
                  placeholder="Technology, Healthcare..."
                  className={inputStyle}
                  style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 rounded-xl text-white font-semibold disabled:opacity-50 flex items-center justify-center gap-2 mt-6 transition-colors hover:opacity-90"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
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
            <Link href={ROUTES.LOGIN} className="font-medium hover:underline gradient-text">
              Sign in
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
