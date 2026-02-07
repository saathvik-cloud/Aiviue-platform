'use client';

import { ROUTES } from '@/constants';
import Image from 'next/image';
import Link from 'next/link';
import { useRef, useEffect, useState } from 'react';
import { Menu } from 'lucide-react';

/**
 * Employer landing page navbar with mobile dropdown for Candidate / Employer links.
 * On mobile: menu icon left of Login opens dropdown with "For Candidates" and "For Employers".
 */
export function EmployerLandingNav() {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <nav className="glass-navbar fixed top-0 left-0 right-0 z-50">
      <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
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

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Mobile: menu button (left of Login) → dropdown with For Candidates / For Employers */}
            <div className="relative sm:hidden" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((o) => !o)}
                className="p-2.5 rounded-xl transition-all hover:bg-white/50"
                style={{ color: 'var(--primary)' }}
                aria-label="Open menu"
                aria-expanded={menuOpen}
              >
                <Menu className="w-5 h-5" />
              </button>
              {menuOpen && (
                <div
                  className="absolute left-0 top-full mt-2 w-48 rounded-xl py-2 shadow-lg z-50 border border-white/20"
                  style={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(12px)',
                  }}
                >
                  <Link
                    href={ROUTES.CANDIDATE_HOME}
                    className="block px-4 py-3 text-sm font-medium transition-colors rounded-lg mx-1 hover:bg-purple-50"
                    style={{ color: 'var(--neutral-dark)' }}
                    onClick={() => setMenuOpen(false)}
                  >
                    For Candidates
                  </Link>
                  <Link
                    href={ROUTES.HOME}
                    className="block px-4 py-3 text-sm font-medium transition-colors rounded-lg mx-1 hover:bg-purple-50"
                    style={{ color: 'var(--neutral-dark)' }}
                    onClick={() => setMenuOpen(false)}
                  >
                    For Employers
                  </Link>
                </div>
              )}
            </div>

            {/* Desktop: For Candidates, For Employers (hidden on mobile) */}
            <Link
              href={ROUTES.CANDIDATE_HOME}
              className="nav-link-gradient px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium rounded-xl transition-all hidden sm:inline-flex"
            >
              For Candidates
            </Link>
            <Link
              href={ROUTES.HOME}
              className="nav-link-gradient px-3 sm:px-4 py-2 sm:py-2.5 text-sm font-medium rounded-xl transition-all hidden sm:inline-flex"
            >
              For Employers
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
              style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
            >
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
