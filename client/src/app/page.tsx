import { ROUTES } from '@/constants';
import Image from 'next/image';
import Link from 'next/link';

/**
 * Home Page - Landing page with glassmorphism design
 */
export default function HomePage() {
  return (
    <main className="min-h-screen gradient-bg relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient orbs */}
        <div 
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-30 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        <div 
          className="absolute top-1/2 -left-40 w-80 h-80 rounded-full opacity-20 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #EC4899 0%, #7C3AED 100%)' }}
        />
        <div 
          className="absolute -bottom-40 right-1/4 w-72 h-72 rounded-full opacity-25 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #7C3AED 100%)' }}
        />
      </div>

      {/* Glassmorphism Navigation */}
      <nav className="glass-navbar fixed top-0 left-0 right-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href={ROUTES.HOME} className="flex items-center gap-2">
              <Image
                src="/aiviue-logo.png"
                alt="AIVIUE"
                width={180}
                height={60}
                className="h-12 sm:h-14 md:h-16 w-auto"
                priority
              />
            </Link>

            {/* Nav Buttons */}
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                href={ROUTES.CANDIDATE_HOME}
                className="px-4 sm:px-5 py-2 sm:py-2.5 text-sm font-medium rounded-xl transition-all border"
                style={{ 
                  color: 'var(--secondary-teal)',
                  borderColor: 'rgba(20, 184, 166, 0.3)',
                  background: 'rgba(20, 184, 166, 0.05)',
                }}
              >
                <span className="hidden sm:inline">For </span>Candidates
              </Link>
              <Link
                href={ROUTES.LOGIN}
                className="btn-glass px-4 sm:px-5 py-2 sm:py-2.5 text-sm font-medium rounded-xl transition-all"
                style={{ color: 'var(--primary)' }}
              >
                Login
              </Link>
              <Link
                href={ROUTES.REGISTER}
                className="px-4 sm:px-5 py-2 sm:py-2.5 text-sm font-medium rounded-xl text-white transition-colors hover:opacity-90"
                style={{ backgroundColor: 'var(--primary)' }}
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 sm:px-6 pt-28 sm:pt-32 pb-12 sm:pb-16 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div 
            className="glass-card inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-8"
          >
            <span className="text-lg">✨</span>
            <span className="gradient-text font-semibold">AI-Powered Hiring Platform</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6" style={{ color: 'var(--neutral-dark)' }}>
            Hire Smarter with{' '}
            <span className="gradient-text">AIVI</span>
          </h1>

          {/* Subheadline */}
          <p className="text-base sm:text-lg lg:text-xl mb-10 max-w-2xl mx-auto px-4" style={{ color: 'var(--neutral-gray)' }}>
            Paste your job description and let our AI extract key details, 
            create structured job posts, and connect with the best candidates.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <Link
              href={ROUTES.REGISTER}
              className="btn-gradient w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-2xl flex items-center justify-center gap-2"
            >
              Get Started Free
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <Link
              href="#features"
              className="btn-glass w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-2xl flex items-center justify-center gap-2"
              style={{ color: 'var(--neutral-dark)' }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Watch Demo
            </Link>
          </div>

          {/* Trust Indicators */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm" style={{ color: 'var(--neutral-muted)' }}>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" style={{ color: 'var(--status-published)' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" style={{ color: 'var(--status-published)' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>14-day free trial</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" style={{ color: 'var(--status-published)' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Cancel anytime</span>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Cards */}
      <section id="features" className="container mx-auto px-4 sm:px-6 py-16 sm:py-20 relative z-10">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4" style={{ color: 'var(--neutral-dark)' }}>
            Why Choose <span className="gradient-text">AIVIUE</span>?
          </h2>
          <p className="text-base sm:text-lg max-w-2xl mx-auto" style={{ color: 'var(--neutral-gray)' }}>
            Streamline your hiring process with AI-powered tools
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 max-w-5xl mx-auto">
          {/* Feature 1 */}
          <div className="glass-card rounded-2xl p-6 sm:p-8">
            <div 
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
            >
              <svg className="w-7 h-7" style={{ color: 'var(--primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-3" style={{ color: 'var(--neutral-dark)' }}>
              Paste & Extract
            </h3>
            <p className="text-sm sm:text-base" style={{ color: 'var(--neutral-gray)' }}>
              Simply paste your job description and let AI extract all key details automatically in seconds.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="glass-card rounded-2xl p-6 sm:p-8">
            <div 
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)' }}
            >
              <svg className="w-7 h-7" style={{ color: 'var(--accent)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-3" style={{ color: 'var(--neutral-dark)' }}>
              Instant Publishing
            </h3>
            <p className="text-sm sm:text-base" style={{ color: 'var(--neutral-gray)' }}>
              Review, edit, and publish your job in seconds. No complex forms to fill or manual data entry.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="glass-card rounded-2xl p-6 sm:p-8 sm:col-span-2 lg:col-span-1">
            <div 
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)' }}
            >
              <svg className="w-7 h-7" style={{ color: 'var(--secondary-teal)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-3" style={{ color: 'var(--neutral-dark)' }}>
              Smart Screening
            </h3>
            <p className="text-sm sm:text-base" style={{ color: 'var(--neutral-gray)' }}>
              Connect to our Screening Agent for automated candidate matching and ranking.
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-4 sm:px-6 py-12 sm:py-16 relative z-10">
        <div className="glass-card rounded-3xl p-8 sm:p-12 max-w-4xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">10K+</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Jobs Posted</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">500+</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Companies</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">95%</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Time Saved</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">4.9★</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>User Rating</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 sm:px-6 py-16 sm:py-20 relative z-10">
        <div 
          className="rounded-3xl p-8 sm:p-12 lg:p-16 text-center text-white relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        >
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white/10 blur-2xl transform translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-white/10 blur-2xl transform -translate-x-1/2 translate-y-1/2" />
          
          <div className="relative z-10">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4">
              Ready to Transform Your Hiring?
            </h2>
            <p className="text-base sm:text-lg opacity-90 max-w-xl mx-auto mb-8">
              Join thousands of companies already using AIVIUE to hire smarter and faster.
            </p>
            <Link
              href={ROUTES.REGISTER}
              className="inline-flex items-center gap-2 px-8 py-4 bg-white rounded-2xl text-base font-semibold transition-all hover:shadow-xl hover:scale-105"
              style={{ color: 'var(--primary)' }}
            >
              Start Free Trial
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t" style={{ borderColor: 'rgba(226, 232, 240, 0.5)' }}>
        <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-8">
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
            <div className="flex items-center gap-3">
              <Image
                src="/aiviue-logo.png"
                alt="AIVIUE"
                width={100}
                height={35}
                className="h-8 w-auto"
              />
              <span className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                © 2026 All rights reserved.
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm" style={{ color: 'var(--neutral-gray)' }}>
              <a href="#" className="hover:text-[var(--primary)] transition-colors">Privacy</a>
              <a href="#" className="hover:text-[var(--primary)] transition-colors">Terms</a>
              <a href="#" className="hover:text-[var(--primary)] transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
