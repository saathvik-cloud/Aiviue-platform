/**
 * Shared UI constants: gradients, job card styles, and common accent styles.
 * Use these for consistent job cards, buttons, and decorative elements across candidate and employer flows.
 */

/** Single gradient string for primary CTA / accent (purple → pink). */
export const PRIMARY_GRADIENT = 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)';

/** Purple → teal (candidate/teal accent). */
export const TEAL_PRIMARY_GRADIENT = 'linear-gradient(135deg, #7C3AED 0%, #14B8A6 100%)';

/** Teal → purple (chat/candidate AIVI accent). */
export const CHAT_ACCENT_GRADIENT = 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)';

/** Teal → purple (hero/landing). */
export const HERO_TEAL_PURPLE_GRADIENT = 'linear-gradient(135deg, #14B8A6 0%, #7C3AED 100%)';

/**
 * Job card gradient variants (bg, border, shadow, accent color, iconBg).
 * Use with index % length for variety on list/grids (e.g. candidate job cards, resume history cards).
 */
export const JOB_CARD_GRADIENTS = [
  {
    bg: 'linear-gradient(145deg, rgba(250, 245, 255, 0.98) 0%, rgba(243, 232, 255, 0.9) 50%, rgba(237, 233, 254, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
    accent: '#7C3AED',
    iconBg: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(240, 253, 250, 0.98) 0%, rgba(220, 245, 238, 0.9) 50%, rgba(204, 251, 241, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(20, 184, 166, 0.1), inset 0 1px 0 rgba(255,255,255,0.5)',
    accent: '#14B8A6',
    iconBg: 'linear-gradient(135deg, rgba(20, 184, 166, 0.15) 0%, rgba(45, 212, 191, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(255, 251, 243, 0.98) 0%, rgba(254, 243, 219, 0.9) 50%, rgba(253, 230, 198, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(245, 158, 11, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
    accent: '#D97706',
    iconBg: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(251, 191, 36, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(253, 242, 248, 0.98) 0%, rgba(252, 231, 243, 0.9) 50%, rgba(249, 168, 212, 0.2) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(236, 72, 153, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
    accent: '#DB2777',
    iconBg: 'linear-gradient(135deg, rgba(236, 72, 153, 0.15) 0%, rgba(168, 85, 247, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(245, 243, 255, 0.98) 0%, rgba(237, 233, 254, 0.9) 50%, rgba(243, 232, 255, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(139, 92, 246, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
    accent: '#8B5CF6',
    iconBg: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(244, 114, 182, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(238, 242, 255, 0.98) 0%, rgba(224, 231, 255, 0.9) 50%, rgba(199, 210, 254, 0.85) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(99, 102, 241, 0.1), inset 0 1px 0 rgba(255,255,255,0.5)',
    accent: '#6366F1',
    iconBg: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(255, 253, 231, 0.98) 0%, rgba(254, 249, 195, 0.9) 50%, rgba(253, 224, 71, 0.15) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(234, 179, 8, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
    accent: '#EAB308',
    iconBg: 'linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(234, 179, 8, 0.12) 100%)',
  },
  {
    bg: 'linear-gradient(145deg, rgba(255, 241, 242, 0.98) 0%, rgba(254, 226, 226, 0.9) 50%, rgba(253, 164, 175, 0.2) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(244, 63, 94, 0.08), inset 0 1px 0 rgba(255,255,255,0.6)',
    accent: '#F43F5E',
    iconBg: 'linear-gradient(135deg, rgba(244, 63, 94, 0.12) 0%, rgba(236, 72, 153, 0.12) 100%)',
  },
] as const;

// ==================== EMPLOYER DASHBOARD LAYOUT ====================

/** Employer sidebar: extreme light pink → light purple gradient (vertical). */
export const EMPLOYER_SIDEBAR_BG =
  'linear-gradient(180deg, rgba(253, 242, 248, 0.98) 0%, rgba(250, 245, 255, 0.98) 50%, rgba(243, 232, 255, 0.95) 100%)';

/** Employer navbar: light pink + violet gradient (stream/light). */
export const EMPLOYER_NAVBAR_BG =
  'linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(124, 58, 237, 0.12) 100%)';

/** Glass card style for employer dashboard (cards/tiles). Use with backdrop blur. */
export const EMPLOYER_GLASS_CARD = {
  background: 'rgba(255, 255, 255, 0.75)',
  backdropFilter: 'blur(16px)',
  WebkitBackdropFilter: 'blur(16px)' as const,
  border: '1px solid rgba(255, 255, 255, 0.6)',
  boxShadow: '0 8px 32px rgba(124, 58, 237, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
} as const;

/**
 * Employer dashboard stat card styles (Total Jobs, Published, Drafts, Closed).
 * Each has cardBg (glass-like gradient bg), gradient (accent), bgLight (icon bg), iconColor.
 */
export const EMPLOYER_STAT_CARD_GRADIENTS = [
  {
    cardBg: 'linear-gradient(145deg, rgba(250, 245, 255, 0.95) 0%, rgba(243, 232, 255, 0.85) 50%, rgba(237, 233, 254, 0.8) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(124, 58, 237, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
    gradient: 'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
    bgLight: 'rgba(124, 58, 237, 0.12)',
    iconColor: '#7C3AED',
  },
  {
    cardBg: 'linear-gradient(145deg, rgba(240, 253, 244, 0.95) 0%, rgba(220, 252, 231, 0.85) 50%, rgba(187, 247, 208, 0.8) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.7)',
    shadow: '0 8px 32px rgba(34, 197, 94, 0.1), inset 0 1px 0 rgba(255,255,255,0.6)',
    gradient: 'linear-gradient(135deg, #22C55E 0%, #4ADE80 100%)',
    bgLight: 'rgba(34, 197, 94, 0.12)',
    iconColor: '#22C55E',
  },
  {
    cardBg: 'linear-gradient(145deg, rgba(255, 251, 235, 0.95) 0%, rgba(254, 243, 199, 0.85) 50%, rgba(253, 230, 138, 0.5) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(245, 158, 11, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
    gradient: 'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)',
    bgLight: 'rgba(245, 158, 11, 0.12)',
    iconColor: '#F59E0B',
  },
  {
    cardBg: 'linear-gradient(145deg, rgba(253, 242, 242, 0.95) 0%, rgba(252, 226, 226, 0.85) 50%, rgba(254, 202, 202, 0.5) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 8px 32px rgba(236, 72, 153, 0.08), inset 0 1px 0 rgba(255,255,255,0.5)',
    gradient: 'linear-gradient(135deg, #EC4899 0%, #F472B6 100%)',
    bgLight: 'rgba(236, 72, 153, 0.12)',
    iconColor: '#EC4899',
  },
] as const;

/**
 * Quick Action card styles (Post a New Job, View All Jobs, Update Profile).
 * Glassmorphic + light gradient per card.
 */
export const EMPLOYER_QUICK_ACTION_CARD_STYLES = [
  {
    cardBg: 'linear-gradient(145deg, rgba(250, 245, 255, 0.9) 0%, rgba(243, 232, 255, 0.85) 50%, rgba(253, 242, 248, 0.8) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.65)',
    shadow: '0 6px 24px rgba(124, 58, 237, 0.08), inset 0 1px 0 rgba(255,255,255,0.6)',
    iconBg: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)',
    iconColor: '#ffffff',
  },
  {
    cardBg: 'linear-gradient(145deg, rgba(245, 243, 255, 0.9) 0%, rgba(237, 233, 254, 0.85) 50%, rgba(255, 255, 255, 0.75) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 6px 24px rgba(124, 58, 237, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
    iconBg: 'linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
    iconColor: '#7C3AED',
  },
  {
    cardBg: 'linear-gradient(145deg, rgba(253, 242, 248, 0.9) 0%, rgba(252, 231, 243, 0.85) 50%, rgba(240, 253, 250, 0.6) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 6px 24px rgba(236, 72, 153, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
    iconBg: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(20, 184, 166, 0.15) 100%)',
    iconColor: '#EC4899',
  },
] as const;

/**
 * Recent Job row card style by status (draft, published, closed).
 * Matches stat card gradient family for consistency.
 */
export const EMPLOYER_RECENT_JOB_ROW_STYLES: Record<string, { cardBg: string; border: string; shadow: string }> = {
  published: {
    cardBg: 'linear-gradient(145deg, rgba(240, 253, 244, 0.92) 0%, rgba(220, 252, 231, 0.85) 50%, rgba(255,255,255,0.7) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.65)',
    shadow: '0 4px 20px rgba(34, 197, 94, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
  },
  draft: {
    cardBg: 'linear-gradient(145deg, rgba(255, 251, 235, 0.92) 0%, rgba(254, 243, 199, 0.85) 50%, rgba(255,255,255,0.7) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 4px 20px rgba(245, 158, 11, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
  },
  closed: {
    cardBg: 'linear-gradient(145deg, rgba(253, 242, 242, 0.92) 0%, rgba(252, 226, 226, 0.85) 50%, rgba(255,255,255,0.7) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 4px 20px rgba(236, 72, 153, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
  },
  default: {
    cardBg: 'linear-gradient(145deg, rgba(250, 245, 255, 0.92) 0%, rgba(243, 232, 255, 0.85) 50%, rgba(255,255,255,0.7) 100%)',
    border: '1px solid rgba(255, 255, 255, 0.6)',
    shadow: '0 4px 20px rgba(124, 58, 237, 0.06), inset 0 1px 0 rgba(255,255,255,0.5)',
  },
};
