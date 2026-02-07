'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

interface SelectDropdownProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

/**
 * Reusable glassmorphism select dropdown component
 */
export function SelectDropdown({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  className = '',
}: SelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close dropdown on escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const selectedOption = options.find(opt => opt.value === value);

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all bg-white/80 hover:bg-white border focus:outline-none focus:ring-2"
        style={{ 
          borderColor: isOpen ? 'var(--primary)' : 'var(--neutral-border)',
          color: selectedOption ? 'var(--neutral-dark)' : 'var(--neutral-gray)',
          '--tw-ring-color': 'var(--primary)',
        } as React.CSSProperties}
      >
        <span className="flex items-center gap-2 truncate">
          {selectedOption?.icon}
          {selectedOption?.label || placeholder}
        </span>
        <ChevronDown 
          className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          style={{ color: 'var(--neutral-gray)' }}
        />
      </button>

      {/* Dropdown Menu – scrollable when many options */}
      {isOpen && (
        <div 
          className="absolute z-50 w-full mt-2 py-1 rounded-xl shadow-xl border overflow-hidden"
          style={{ 
            background: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderColor: 'var(--neutral-border)',
            boxShadow: '0 10px 40px rgba(124, 58, 237, 0.15)',
          }}
        >
          <div className="max-h-60 overflow-y-auto overflow-x-hidden py-1">
          {options.map((option) => {
            const isSelected = option.value === value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className="w-full flex items-center justify-between gap-2 px-4 py-2.5 text-sm transition-colors text-left"
                style={{ 
                  backgroundColor: isSelected ? 'var(--primary-50)' : 'transparent',
                  color: isSelected ? 'var(--primary)' : 'var(--neutral-dark)',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.backgroundColor = 'var(--neutral-light)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected ? 'var(--primary-50)' : 'transparent';
                }}
              >
                <span className="flex items-center gap-2">
                  {option.icon}
                  {option.label}
                </span>
                {isSelected && (
                  <Check className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                )}
              </button>
            );
          })}
          </div>
        </div>
      )}
    </div>
  );
}

export default SelectDropdown;
