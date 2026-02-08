/**
 * Utility Functions
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge class names with Tailwind support
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format date
 */
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  };
  return new Date(date).toLocaleDateString('en-US', defaultOptions);
}

/**
 * Format date with time
 */
export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format relative time
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return formatDate(date);
}

/**
 * Currency code to symbol (for job cards / salary display).
 * Matches backend job.currency: INR, USD, GBP, EUR, AUD, CAD, etc.
 */
const CURRENCY_SYMBOLS: Record<string, string> = {
  INR: '₹',
  USD: '$',
  GBP: '£',
  EUR: '€',
  AUD: 'A$',
  CAD: 'C$',
};

export function getCurrencySymbol(currency: string | undefined | null): string {
  if (!currency) return '$';
  const code = currency.toUpperCase();
  return CURRENCY_SYMBOLS[code] ?? currency;
}

/** Strip currency symbols from backend salary_range so UI can show a single symbol from getCurrencySymbol(currency). */
export function stripSalaryRangeCurrency(salaryRange: string | undefined | null): string {
  if (!salaryRange || typeof salaryRange !== 'string') return salaryRange ?? '';
  return salaryRange.replace(/[$₹£€]/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Format currency
 */
export function formatCurrency(amount: number, currency = 'USD'): string {
  const code = currency && CURRENCY_SYMBOLS[currency.toUpperCase()] ? currency : 'USD';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: code,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format salary range with optional currency (default USD).
 */
export function formatSalaryRange(
  min?: number,
  max?: number,
  currency?: string | null
): string {
  const code = currency || 'USD';
  if (!min && !max) return 'Not specified';
  if (min && !max) return `${formatCurrency(min, code)}+`;
  if (!min && max) return `Up to ${formatCurrency(max, code)}`;
  return `${formatCurrency(min!, code)} - ${formatCurrency(max!, code)}`;
}

/**
 * Truncate text
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}

/**
 * Capitalize first letter
 */
export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

/**
 * Get initials from name
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Sleep/delay
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if empty
 */
export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}
