'use client';

import { CANDIDATE_NAV_ITEMS, ROUTES } from '@/constants';
import { getInitials } from '@/lib/utils';
import { useCandidateAuthStore } from '@/stores';
import {
    Briefcase,
    ChevronDown,
    FileText,
    HelpCircle,
    LayoutDashboard,
    LogOut,
    Menu,
    Settings,
    User,
    X,
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

/**
 * Icon map for dynamic rendering from string icon names in CANDIDATE_NAV_ITEMS.
 * Dictionary dispatch pattern -- maps string keys to Lucide icon components.
 */
const iconMap: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  LayoutDashboard,
  FileText,
  Briefcase,
  User,
};

/**
 * Page title resolver -- dictionary dispatch for header title.
 * Returns the appropriate title based on the current pathname.
 */
const PAGE_TITLE_MAP: Record<string, string> = {
  [ROUTES.CANDIDATE_DASHBOARD]: 'Dashboard',
  [ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE]: 'Complete Profile',
  [ROUTES.CANDIDATE_DASHBOARD_RESUME]: 'Resume',
  [ROUTES.CANDIDATE_DASHBOARD_RESUME_NEW]: 'Build Resume',
  [ROUTES.CANDIDATE_DASHBOARD_PROFILE]: 'Profile',
  [ROUTES.CANDIDATE_DASHBOARD_JOBS]: 'Jobs',
};

function getPageTitle(pathname: string): string {
  // Exact match first
  if (PAGE_TITLE_MAP[pathname]) return PAGE_TITLE_MAP[pathname];

  // Prefix match for sub-routes
  const match = Object.entries(PAGE_TITLE_MAP).find(
    ([route]) => route !== ROUTES.CANDIDATE_DASHBOARD && pathname.startsWith(route)
  );
  return match ? match[1] : 'Dashboard';
}

/**
 * Candidate Dashboard Layout
 *
 * Protected layout wrapping all /candidate/dashboard/* routes.
 * Mirrors the employer DashboardLayout but uses candidate auth store
 * and candidate-specific navigation items.
 */
export default function CandidateDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { candidate, isAuthenticated, clearCandidate, isLoading } =
    useCandidateAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Protected route: redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.CANDIDATE_LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Require complete profile: if status is basic, redirect to complete-profile unless already there
  useEffect(() => {
    if (isLoading || !isAuthenticated || !candidate) return;
    if (candidate.profile_status === 'basic' && pathname !== ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE) {
      router.replace(ROUTES.CANDIDATE_DASHBOARD_COMPLETE_PROFILE);
    }
  }, [candidate?.profile_status, isAuthenticated, isLoading, pathname, router]);

  const handleLogout = () => {
    clearCandidate();
    router.push(ROUTES.CANDIDATE_HOME);
  };

  // Loading state while hydrating auth from localStorage
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div
          className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin"
          style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }}
        />
      </div>
    );
  }

  // Guard: don't render dashboard if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex gradient-bg">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar – violet / pink gradient */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 flex flex-col
          transform transition-transform duration-300 ease-out
          lg:transform-none shadow-xl
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        style={{
          background:
            'linear-gradient(180deg, #FDF2F8 0%, #FCE7F3 25%, #FBCFE8 50%, #F5D0FE 75%, #EDE9FE 100%)',
          borderRight: '1px solid rgba(236, 72, 153, 0.15)',
          boxShadow: '4px 0 24px rgba(124, 58, 237, 0.06)',
        }}
      >
        {/* Logo + Candidate Badge */}
        <div className="p-4 sm:p-5 flex items-center justify-between">
          <Link href={ROUTES.CANDIDATE_DASHBOARD} className="flex items-center gap-2">
            <Image
              src="/aiviue-logo.png"
              alt="AIVIUE"
              width={180}
              height={60}
              className="h-14 sm:h-16 w-auto"
              priority
            />
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
            style={{ color: 'var(--neutral-gray)' }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Candidate Portal Badge */}
        <div className="px-4 sm:px-5 pb-3">
          <span
            className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider"
            style={{
              background: 'rgba(236, 72, 153, 0.15)',
              color: '#BE185D',
              border: '1px solid rgba(236, 72, 153, 0.25)',
            }}
          >
            Candidate
          </span>
        </div>

        {/* Navigation – active: light pink/violet */}
        <nav className="flex-1 px-2 sm:px-3 py-4 space-y-0.5">
          <p
            className="px-3 text-xs font-semibold uppercase tracking-wider mb-3"
            style={{ color: 'var(--neutral-muted)' }}
          >
            General
          </p>
          {CANDIDATE_NAV_ITEMS.map((item) => {
            const Icon = iconMap[item.icon];
            const isActive =
              item.href === ROUTES.CANDIDATE_DASHBOARD
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(item.href + '/');

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all"
                style={{
                  backgroundColor: isActive ? 'rgba(236, 72, 153, 0.12)' : 'transparent',
                  color: isActive ? '#9D174D' : 'var(--neutral-gray)',
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'rgba(236, 72, 153, 0.06)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {Icon && <Icon className="w-5 h-5 shrink-0" />}
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Build Resume CTA - Hide when already on resume pages */}
        {!pathname.startsWith(ROUTES.CANDIDATE_DASHBOARD_RESUME) && (
          <div className="px-3 py-4">
            <Link
              href={ROUTES.CANDIDATE_DASHBOARD_RESUME}
              onClick={() => setSidebarOpen(false)}
              className="btn-gradient flex items-center justify-center gap-2 w-full py-3 rounded-xl text-sm font-semibold"
            >
              <FileText className="w-5 h-5" />
              Build Resume
            </Link>
          </div>
        )}

        {/* User Info at bottom */}
        <div className="p-4" style={{ borderTop: '1px solid var(--neutral-border)' }}>
          <div className="flex items-center gap-3">
            {candidate?.profile_photo_url ? (
              <img
                src={candidate.profile_photo_url}
                alt={candidate.name || 'Profile'}
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold text-white"
                style={{ backgroundColor: 'var(--secondary-teal)' }}
              >
                {candidate ? getInitials(candidate.name) : '?'}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p
                className="text-sm font-medium truncate"
                style={{ color: 'var(--neutral-dark)' }}
              >
                {candidate?.name || 'Candidate'}
              </p>
              <p className="text-xs truncate" style={{ color: 'var(--neutral-gray)' }}>
                +91 {candidate?.mobile || ''}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Top Header – light pink/violet tint to match sidebar */}
        <header
          className="sticky top-0 z-30 px-4 sm:px-6 py-2 flex items-center justify-between min-h-[56px]"
          style={{
            background: 'linear-gradient(90deg, rgba(253, 242, 248, 0.95) 0%, rgba(252, 231, 243, 0.9) 50%, rgba(255, 255, 255, 0.95) 100%)',
            backdropFilter: 'blur(12px)',
            borderBottom: '1px solid rgba(236, 72, 153, 0.1)',
            boxShadow: '0 2px 12px rgba(124, 58, 237, 0.04)',
          }}
        >
          {/* Mobile Menu Button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-xl hover:bg-white/50 transition-colors"
            style={{ color: 'var(--neutral-gray)' }}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Page Title */}
          <div className="hidden lg:block">
            <h1
              className="text-lg font-semibold"
              style={{ color: 'var(--neutral-dark)' }}
            >
              {getPageTitle(pathname)}
            </h1>
          </div>

          {/* Right side - User Menu */}
          <div className="relative ml-auto">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 p-1.5 sm:p-2 rounded-xl hover:bg-white/50 transition-colors"
            >
              {candidate?.profile_photo_url ? (
                <img
                  src={candidate.profile_photo_url}
                  alt={candidate.name || 'Profile'}
                  className="w-9 h-9 rounded-full object-cover"
                />
              ) : (
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-semibold"
                  style={{ backgroundColor: 'var(--secondary-teal)' }}
                >
                  {candidate ? getInitials(candidate.name) : '?'}
                </div>
              )}
              <span
                className="hidden sm:block text-sm font-medium"
                style={{ color: 'var(--neutral-dark)' }}
              >
                {candidate?.name?.split(' ')[0] || 'User'}
              </span>
              <ChevronDown
                className="w-4 h-4 hidden sm:block"
                style={{ color: 'var(--neutral-gray)' }}
              />
            </button>

            {/* User Dropdown Menu */}
            {userMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setUserMenuOpen(false)}
                />
                <div className="glass-dropdown absolute right-0 mt-2 w-56 rounded-2xl py-2 z-50">
                  {/* User info header */}
                  <div
                    className="px-4 py-3 border-b"
                    style={{ borderColor: 'var(--neutral-border)' }}
                  >
                    <p
                      className="text-sm font-medium"
                      style={{ color: 'var(--neutral-dark)' }}
                    >
                      {candidate?.name}
                    </p>
                    <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                      +91 {candidate?.mobile}
                    </p>
                  </div>

                  {/* Menu items */}
                  <div className="py-1">
                    <Link
                      href={ROUTES.CANDIDATE_DASHBOARD_PROFILE}
                      onClick={() => setUserMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-[var(--primary-50)] transition-colors"
                      style={{ color: 'var(--neutral-dark)' }}
                    >
                      <User
                        className="w-4 h-4"
                        style={{ color: 'var(--neutral-gray)' }}
                      />
                      Profile
                    </Link>
                    <Link
                      href={ROUTES.CANDIDATE_DASHBOARD_PROFILE}
                      onClick={() => setUserMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-[var(--primary-50)] transition-colors"
                      style={{ color: 'var(--neutral-dark)' }}
                    >
                      <Settings
                        className="w-4 h-4"
                        style={{ color: 'var(--neutral-gray)' }}
                      />
                      Settings
                    </Link>
                    <a
                      href="#"
                      className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-[var(--primary-50)] transition-colors"
                      style={{ color: 'var(--neutral-dark)' }}
                    >
                      <HelpCircle
                        className="w-4 h-4"
                        style={{ color: 'var(--neutral-gray)' }}
                      />
                      Help Center
                    </a>
                  </div>

                  {/* Logout */}
                  <div
                    className="border-t py-1"
                    style={{ borderColor: 'var(--neutral-border)' }}
                  >
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-red-50 transition-colors w-full text-left"
                      style={{ color: 'var(--status-closed)' }}
                    >
                      <LogOut className="w-4 h-4" />
                      Sign out
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
