'use client';

/**
 * ProfileStyleSelect - Dropdown that matches the profile menu look (rounded card, icon + text, separators).
 * Supports "Or type your own" with normalized matching (case, hyphen, spaces) so e.g. "backend developer" matches "Backend Developer".
 * Renders dropdown in a portal so it appears above sibling sections (avoids z-index/stacking and overflow clipping).
 */

import { useRef, useEffect, useLayoutEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown, Check } from 'lucide-react';

export interface ProfileStyleSelectOption {
  value: string;
  label: string;
  slug?: string;
}

interface ProfileStyleSelectProps {
  options: ProfileStyleSelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  allowCustom?: boolean;
  customPlaceholder?: string;
  icon?: React.ReactNode;
  /** Label for the field (shown above) */
  label?: string;
  className?: string;
}

/** Normalize for matching: lowercase, hyphens to spaces, collapse spaces, trim. */
export function normalizeForMatch(s: string): string {
  return (s || '')
    .toLowerCase()
    .replace(/-/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Normalize and remove spaces so "back end developer" matches "Backend Developer". */
function normalizeNoSpaces(s: string): string {
  return normalizeForMatch(s).replace(/\s/g, '');
}

/** Check if user input matches option (by label or slug); allows minor spelling/space variance. */
function optionMatchesInput(option: ProfileStyleSelectOption, input: string): boolean {
  const normalized = normalizeForMatch(input);
  if (!normalized) return false;
  const labelNorm = normalizeForMatch(option.label);
  const slugNorm = option.slug ? normalizeForMatch(option.slug) : '';
  const inputNoSpaces = normalizeNoSpaces(input);
  const labelNoSpaces = labelNorm.replace(/\s/g, '');
  const slugNoSpaces = slugNorm.replace(/\s/g, '');
  return (
    labelNorm === normalized ||
    slugNorm === normalized ||
    labelNorm.includes(normalized) ||
    slugNorm.includes(normalized) ||
    labelNoSpaces === inputNoSpaces ||
    slugNoSpaces === inputNoSpaces ||
    labelNoSpaces.includes(inputNoSpaces) ||
    slugNoSpaces.includes(inputNoSpaces)
  );
}

export function ProfileStyleSelect({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  disabled = false,
  isLoading = false,
  allowCustom = false,
  customPlaceholder = 'Or type your own',
  icon,
  label,
  className = '',
}: ProfileStyleSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customInput, setCustomInput] = useState('');
  const [dropdownPosition, setDropdownPosition] = useState<{ top: number; left: number; width: number } | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectedOption = options.find((o) => o.value === value);

  // Position dropdown under trigger (for portal). Fixed = viewport-relative.
  useLayoutEffect(() => {
    if (!isOpen || typeof document === 'undefined') return;
    const el = dropdownRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setDropdownPosition({
      top: rect.bottom,
      left: rect.left,
      width: rect.width,
    });
  }, [isOpen]);

  const updatePosition = () => {
    const el = dropdownRef.current;
    if (!el || !isOpen) return;
    const rect = el.getBoundingClientRect();
    setDropdownPosition({
      top: rect.bottom,
      left: rect.left,
      width: rect.width,
    });
  };

  useEffect(() => {
    if (!isOpen) return;
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);
    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      const inTrigger = dropdownRef.current?.contains(target);
      const inPanel = panelRef.current?.contains(target);
      if (!inTrigger && !inPanel) {
        setIsOpen(false);
        setDropdownPosition(null);
        if (allowCustom && customInput.trim()) {
          const match = options.find((o) => optionMatchesInput(o, customInput));
          if (match) {
            onChange(match.value);
            setCustomInput('');
          }
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [allowCustom, customInput, options, onChange]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        setDropdownPosition(null);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const filteredOptions = allowCustom && customInput.trim()
    ? options.filter((o) => optionMatchesInput(o, customInput))
    : options;

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setCustomInput('');
    setIsOpen(false);
    setDropdownPosition(null);
  };

  const handleCustomKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && customInput.trim()) {
      const match = options.find((o) => optionMatchesInput(o, customInput));
      if (match) {
        handleSelect(match.value);
      }
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
          {label}
        </label>
      )}
      <div ref={dropdownRef} className="relative">
        <button
          type="button"
          onClick={() => !disabled && !isLoading && setIsOpen((o) => !o)}
          disabled={disabled || isLoading}
          className="w-full flex items-center justify-between gap-2 px-4 py-3 rounded-2xl text-sm transition-all border focus:outline-none focus:ring-2 focus:ring-teal-500/30"
          style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderColor: isOpen ? 'var(--primary)' : 'var(--neutral-border)',
            color: selectedOption ? 'var(--neutral-dark)' : 'var(--neutral-gray)',
          }}
        >
          <span className="flex items-center gap-2 truncate">
            {icon && <span style={{ color: 'var(--neutral-gray)' }}>{icon}</span>}
            {selectedOption?.label || placeholder}
          </span>
          {isLoading ? (
            <span className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          ) : (
            <ChevronDown
              className={`w-4 h-4 flex-shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`}
              style={{ color: 'var(--neutral-gray)' }}
            />
          )}
        </button>

        {isOpen &&
          typeof document !== 'undefined' &&
          createPortal(
            <div
              ref={panelRef}
              className="fixed rounded-2xl py-2 overflow-hidden mt-2"
              style={{
                top: dropdownPosition?.top ?? 0,
                left: dropdownPosition?.left ?? 0,
                width: dropdownPosition?.width ?? 240,
                zIndex: 9999,
                background: 'rgba(255, 255, 255, 0.98)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: '1px solid rgba(226, 232, 240, 0.8)',
                boxShadow: '0 10px 40px rgba(124, 58, 237, 0.15)',
              }}
            >
              <div className="py-1 max-h-60 overflow-y-auto overflow-x-hidden">
                {filteredOptions.map((option) => {
                  const isSelected = option.value === value;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => handleSelect(option.value)}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors hover:bg-[var(--primary-50)]"
                      style={{
                        color: isSelected ? 'var(--primary)' : 'var(--neutral-dark)',
                        backgroundColor: isSelected ? 'var(--primary-50)' : 'transparent',
                      }}
                    >
                      {icon && <span style={{ color: 'var(--neutral-gray)' }}>{icon}</span>}
                      <span className="flex-1 truncate">{option.label}</span>
                      {isSelected && <Check className="w-4 h-4 flex-shrink-0" style={{ color: 'var(--primary)' }} />}
                    </button>
                  );
                })}
              </div>

              {allowCustom && (
                <div
                  className="border-t px-3 py-2"
                  style={{ borderColor: 'var(--neutral-border)' }}
                >
                  <input
                    ref={inputRef}
                    type="text"
                    value={customInput}
                    onChange={(e) => setCustomInput(e.target.value)}
                    onKeyDown={handleCustomKeyDown}
                    placeholder={customPlaceholder}
                    className="w-full px-3 py-2 rounded-xl text-sm border"
                    style={{
                      borderColor: 'var(--neutral-border)',
                      background: 'rgba(246, 239, 214, 0.3)',
                      color: 'var(--text-primary)',
                    }}
                  />
                </div>
              )}
            </div>,
            document.body
          )}
      </div>
    </div>
  );
}

export default ProfileStyleSelect;
