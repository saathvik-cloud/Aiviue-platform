'use client';

import { Loader2, Send } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface ChatInputProps {
    onSend: (message: string) => void;
    placeholder?: string;
    inputType?: 'text' | 'textarea' | 'number';
    disabled?: boolean;
    isLoading?: boolean;
    minLength?: number;
    autoFocus?: boolean;
}

/**
 * ChatInput - Bottom input bar for typing messages.
 * Supports text, textarea, and number inputs.
 */
export function ChatInput({
    onSend,
    placeholder = 'Type your message...',
    inputType = 'text',
    disabled = false,
    isLoading = false,
    minLength = 0,
    autoFocus = true,
}: ChatInputProps) {
    const [value, setValue] = useState('');
    const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

    useEffect(() => {
        if (autoFocus && inputRef.current) {
            inputRef.current.focus();
        }
    }, [autoFocus, inputType]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();

        if (!value.trim() || value.length < minLength || disabled || isLoading) {
            return;
        }

        onSend(value.trim());
        setValue('');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey && inputType !== 'textarea') {
            e.preventDefault();
            handleSubmit();
        }
    };

    const isValid = value.trim().length >= minLength;

    return (
        <form
            onSubmit={handleSubmit}
            className="chat-input-container px-4 py-4 border-t"
            style={{
                background: 'rgba(255, 255, 255, 0.4)',
                backdropFilter: 'blur(10px)',
                borderColor: 'rgba(124, 58, 237, 0.1)'
            }}
        >
            <div
                className={`flex items-center gap-3 p-1.5 pl-4 rounded-2xl transition-all duration-300 ${!disabled && !isLoading ? 'hover:shadow-lg hover:shadow-purple-500/5' : ''
                    }`}
                style={{
                    background: 'white',
                    border: '1px solid rgba(124, 58, 237, 0.15)',
                    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.02)'
                }}
            >
                {inputType === 'textarea' ? (
                    <textarea
                        ref={inputRef as React.RefObject<HTMLTextAreaElement>}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder}
                        disabled={disabled || isLoading}
                        rows={1}
                        className="flex-1 bg-transparent py-2.5 px-1 text-sm resize-none border-none outline-none focus:ring-0 placeholder:text-neutral-400 custom-scrollbar"
                        style={{
                            color: 'var(--neutral-dark)',
                            minHeight: '40px',
                            maxHeight: '120px'
                        }}
                    />
                ) : (
                    <input
                        ref={inputRef as React.RefObject<HTMLInputElement>}
                        type={inputType === 'number' ? 'number' : 'text'}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder}
                        disabled={disabled || isLoading}
                        className="flex-1 bg-transparent py-2.5 px-1 text-sm border-none outline-none focus:ring-0 placeholder:text-neutral-400"
                        style={{ color: 'var(--neutral-dark)' }}
                    />
                )}

                <button
                    type="submit"
                    disabled={!isValid || disabled || isLoading}
                    className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-md"
                    style={{
                        background: isValid
                            ? 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)'
                            : 'var(--neutral-gray)',
                        color: 'white',
                        boxShadow: isValid ? '0 4px 12px rgba(124, 58, 23, 0.3)' : 'none',
                    }}
                >
                    {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Send className={`w-4 h-4 ${isValid ? 'translate-x-0.5 -translate-y-0.5' : ''}`} />
                    )}
                </button>
            </div>

            {minLength > 0 && (
                <div className="flex justify-end items-center mt-2 px-2">
                    <p className="text-[10px] font-semibold tracking-wider" style={{ color: isValid ? 'var(--status-published)' : 'var(--neutral-gray)' }}>
                        {value.length} / {minLength} CHARS
                    </p>
                </div>
            )}
        </form>
    );
}
