import { ROUTES } from '@/constants';
import Image from 'next/image';
import Link from 'next/link';

/**
 * Candidate Landing Page - Dedicated entry point for job seekers.
 *
 * Design: Same glassmorphism + gradient theme as the employer landing page.
 * Flow: Candidate → Login/Signup → Basic Profile → Dashboard (Resume Builder + Jobs)
 */
export default function CandidateLandingPage() {
  return (
    <main className="min-h-screen gradient-bg relative overflow-hidden">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute -top-40 -right-40 w-96 h-96 rounded-full opacity-30 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #14B8A6 0%, #7C3AED 100%)' }}
        />
        <div
          className="absolute top-1/2 -left-40 w-80 h-80 rounded-full opacity-20 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        <div
          className="absolute -bottom-40 right-1/4 w-72 h-72 rounded-full opacity-25 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #EC4899 0%, #14B8A6 100%)' }}
        />
      </div>

      {/* Glassmorphism Navigation */}
      <nav className="glass-navbar fixed top-0 left-0 right-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            {/* Logo + Candidate Badge */}
            <div className="flex items-center gap-3">
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
              <span
                className="hidden sm:inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                style={{
                  background: 'rgba(20, 184, 166, 0.1)',
                  color: 'var(--secondary-teal)',
                  border: '1px solid rgba(20, 184, 166, 0.3)',
                }}
              >
                For Candidates
              </span>
            </div>

            {/* Auth Buttons */}
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                href={ROUTES.HOME}
                className="btn-glass px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium rounded-xl transition-all hidden sm:inline-flex"
                style={{ color: 'var(--neutral-gray)' }}
              >
                For Employers
              </Link>
              <Link
                href={ROUTES.CANDIDATE_LOGIN}
                className="btn-glass px-4 sm:px-5 py-2 sm:py-2.5 text-sm font-medium rounded-xl transition-all"
                style={{ color: 'var(--primary)' }}
              >
                Login
              </Link>
              <Link
                href={ROUTES.CANDIDATE_REGISTER}
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
          <div className="glass-card inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-8">
            <span className="text-lg">🚀</span>
            <span className="gradient-text font-semibold">Your Career Starts Here</span>
          </div>

          {/* Headline */}
          <h1
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6"
            style={{ color: 'var(--neutral-dark)' }}
          >
            Build Your Resume with{' '}
            <span className="gradient-text">AIVI</span>
          </h1>

          {/* Subheadline */}
          <p
            className="text-base sm:text-lg lg:text-xl mb-10 max-w-2xl mx-auto px-4"
            style={{ color: 'var(--neutral-gray)' }}
          >
            Create a professional resume in minutes using our AI assistant.
            Upload your existing resume or let AIVI guide you step by step
            — then discover jobs that match your skills.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <Link
              href={ROUTES.CANDIDATE_REGISTER}
              className="btn-gradient w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-2xl flex items-center justify-center gap-2"
            >
              Create My Resume
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <Link
              href="#how-it-works"
              className="btn-glass w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-2xl flex items-center justify-center gap-2"
              style={{ color: 'var(--neutral-dark)' }}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              How It Works
            </Link>
          </div>

          {/* Trust Indicators */}
          <div
            className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm"
            style={{ color: 'var(--neutral-muted)' }}
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" style={{ color: 'var(--status-published)' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>100% Free to use</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" style={{ color: 'var(--status-published)' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>AI-powered resume builder</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" style={{ color: 'var(--status-published)' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Smart job matching</span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="container mx-auto px-4 sm:px-6 py-16 sm:py-20 relative z-10">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4" style={{ color: 'var(--neutral-dark)' }}>
            How <span className="gradient-text">AIVI</span> Works for You
          </h2>
          <p className="text-base sm:text-lg max-w-2xl mx-auto" style={{ color: 'var(--neutral-gray)' }}>
            Three simple steps to land your next job
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 max-w-5xl mx-auto">
          {/* Step 1 */}
          <div className="glass-card rounded-2xl p-6 sm:p-8 relative">
            <div
              className="absolute -top-3 -left-3 w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold"
              style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
            >
              1
            </div>
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
            >
              <svg className="w-7 h-7" style={{ color: 'var(--primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-3" style={{ color: 'var(--neutral-dark)' }}>
              Sign Up in Seconds
            </h3>
            <p className="text-sm sm:text-base" style={{ color: 'var(--neutral-gray)' }}>
              Just enter your mobile number and basic details. No lengthy forms, no hassle.
            </p>
          </div>

          {/* Step 2 */}
          <div className="glass-card rounded-2xl p-6 sm:p-8 relative">
            <div
              className="absolute -top-3 -left-3 w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold"
              style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
            >
              2
            </div>
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)' }}
            >
              <svg className="w-7 h-7" style={{ color: 'var(--accent)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-3" style={{ color: 'var(--neutral-dark)' }}>
              Build Your Resume
            </h3>
            <p className="text-sm sm:text-base" style={{ color: 'var(--neutral-gray)' }}>
              Upload your existing resume PDF or let AIVI bot ask you smart questions to create one for you.
            </p>
          </div>

          {/* Step 3 */}
          <div className="glass-card rounded-2xl p-6 sm:p-8 sm:col-span-2 lg:col-span-1 relative">
            <div
              className="absolute -top-3 -left-3 w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold"
              style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
            >
              3
            </div>
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
              style={{ background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)' }}
            >
              <svg className="w-7 h-7" style={{ color: 'var(--secondary-teal)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-3" style={{ color: 'var(--neutral-dark)' }}>
              Discover Matching Jobs
            </h3>
            <p className="text-sm sm:text-base" style={{ color: 'var(--neutral-gray)' }}>
              Get personalized job recommendations based on your skills, location, and salary preferences.
            </p>
          </div>
        </div>
      </section>

      {/* Why AIVI Section */}
      <section className="container mx-auto px-4 sm:px-6 py-12 sm:py-16 relative z-10">
        <div className="glass-card rounded-3xl p-8 sm:p-12 max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold mb-8 text-center" style={{ color: 'var(--neutral-dark)' }}>
            Why Build Your Resume with <span className="gradient-text">AIVI</span>?
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {[
              {
                icon: '🤖',
                title: 'AI-Powered Questions',
                desc: 'AIVI adapts questions based on your chosen role — delivery boy, telecaller, software developer, or designer.',
              },
              {
                icon: '📄',
                title: 'Upload or Create',
                desc: 'Already have a resume? Upload it and we fill in the gaps. Starting fresh? Our bot guides you.',
              },
              {
                icon: '💼',
                title: 'Job Matching',
                desc: 'Your resume data powers smart job recommendations from real employers on our platform.',
              },
              {
                icon: '📱',
                title: 'Mobile Friendly',
                desc: 'Sign up with your mobile number and build your resume from any device, anywhere.',
              },
            ].map((item) => (
              <div key={item.title} className="flex gap-4">
                <div className="text-2xl flex-shrink-0 mt-1">{item.icon}</div>
                <div>
                  <h3 className="font-semibold mb-1" style={{ color: 'var(--neutral-dark)' }}>
                    {item.title}
                  </h3>
                  <p className="text-sm" style={{ color: 'var(--neutral-gray)' }}>
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-4 sm:px-6 py-12 sm:py-16 relative z-10">
        <div className="glass-card rounded-3xl p-8 sm:p-12 max-w-4xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">50K+</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Resumes Built</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">10K+</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Active Jobs</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">2 min</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Avg. Resume Time</div>
            </div>
            <div className="text-center">
              <div className="text-3xl sm:text-4xl font-bold gradient-text mb-2">4.8★</div>
              <div className="text-sm" style={{ color: 'var(--neutral-gray)' }}>Candidate Rating</div>
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
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white/10 blur-2xl transform translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-white/10 blur-2xl transform -translate-x-1/2 translate-y-1/2" />

          <div className="relative z-10">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-4">
              Ready to Land Your Dream Job?
            </h2>
            <p className="text-base sm:text-lg opacity-90 max-w-xl mx-auto mb-8">
              Create your resume in minutes and start getting matched with the best opportunities.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
              <Link
                href={ROUTES.CANDIDATE_REGISTER}
                className="inline-flex items-center gap-2 px-8 py-4 bg-white rounded-2xl text-base font-semibold transition-all hover:shadow-xl hover:scale-105"
                style={{ color: 'var(--primary)' }}
              >
                Get Started Free
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link
                href={ROUTES.CANDIDATE_LOGIN}
                className="inline-flex items-center gap-2 px-8 py-4 bg-white/20 backdrop-blur-sm border border-white/30 rounded-2xl text-base font-semibold text-white transition-all hover:bg-white/30"
              >
                Already have an account? Login
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Explore Jobs Teaser */}
      <section className="container mx-auto px-4 sm:px-6 py-12 sm:py-16 relative z-10">
        <div className="text-center max-w-2xl mx-auto">
          <h3 className="text-xl sm:text-2xl font-bold mb-3" style={{ color: 'var(--neutral-dark)' }}>
            Explore Jobs Across Industries
          </h3>
          <p className="text-sm sm:text-base mb-6" style={{ color: 'var(--neutral-gray)' }}>
            From delivery to software development — find opportunities that match your skills.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
            {[
              'Delivery & Logistics',
              'Telecalling & BPO',
              'IT & Software',
              'Sales & Marketing',
              'Design & Creative',
              'Hospitality',
              'Healthcare',
              'Retail',
            ].map((category) => (
              <span
                key={category}
                className="glass-card px-4 py-2 rounded-full text-xs sm:text-sm font-medium cursor-default"
                style={{ color: 'var(--neutral-dark)' }}
              >
                {category}
              </span>
            ))}
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
              <Link href={ROUTES.HOME} className="hover:text-[var(--primary)] transition-colors">
                For Employers
              </Link>
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
