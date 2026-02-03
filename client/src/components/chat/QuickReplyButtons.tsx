'use client';

import type { ChatButton } from '@/types';

interface QuickReplyButtonsProps {
    buttons: ChatButton[];
    onSelect: (button: ChatButton) => void;
    disabled?: boolean;
}

/**
 * QuickReplyButtons - Renders clickable button options for chat.
 * Supports multiple variants and smooth animations.
 */
export function QuickReplyButtons({
    buttons,
    onSelect,
    disabled = false,
}: QuickReplyButtonsProps) {
    return (
        <div className="flex flex-wrap gap-2 mt-3">
            {buttons.map((button, index) => (
                <button
                    key={button.id}
                    onClick={() => onSelect(button)}
                    disabled={disabled}
                    className="quick-reply-btn px-4 py-2.5 rounded-xl text-sm font-medium transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                        background: button.variant === 'primary'
                            ? 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)'
                            : 'rgba(255, 255, 255, 0.9)',
                        color: button.variant === 'primary' ? 'white' : 'var(--neutral-dark)',
                        border: button.variant === 'primary'
                            ? 'none'
                            : '1px solid var(--neutral-border)',
                        boxShadow: button.variant === 'primary'
                            ? '0 4px 15px rgba(124, 58, 237, 0.25)'
                            : '0 2px 8px rgba(0, 0, 0, 0.04)',
                        animationDelay: `${index * 50}ms`,
                    }}
                >
                    {button.label}
                </button>
            ))}
        </div>
    );
}
