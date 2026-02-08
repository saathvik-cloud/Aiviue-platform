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
