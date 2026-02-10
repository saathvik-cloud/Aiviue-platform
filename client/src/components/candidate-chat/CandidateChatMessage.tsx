'use client';

/**
 * CandidateChatMessage - Renders individual chat messages for the resume builder bot.
 *
 * Supports multiple message types:
 * - text: Simple text message
 * - buttons: Multiple choice buttons
 * - loading: Progress/thinking indicator
 * - error: Error message with retry
 * - resume_preview: Resume preview card
 * - multi_select: Multi-selection with suggestion buttons + Custom
 * - input_*: Various input prompts
 * - progress: Progress indicator with percentage
 * - boolean: Yes/No buttons
 *
 * Follows the same design patterns as employer ChatMessage.
 */

import type { CandidateChatButton, CandidateChatMessage as CandidateChatMessageType } from '@/types';
import { Check, Download, FileText, Plus, Upload, X } from 'lucide-react';
import Image from 'next/image';
import { useCallback, useState } from 'react';

interface CandidateChatMessageProps {
    message: CandidateChatMessageType;
    onButtonClick?: (button: CandidateChatButton) => void;
    onRetry?: () => void;
    onDownloadResume?: (resumeId: string) => void;
    onMultiSelectSubmit?: (questionKey: string, values: string[]) => void;
    isLatest?: boolean;
    showAvatar?: boolean;
    /** Used to avoid overlap when "Would you like to save?" follows resume preview card */
    previousMessageType?: string;
}

/** Renders bot content and converts **bold** to <strong> for better UX. */
function BotContent({ content, className = '' }: { content: string; className?: string }) {
    if (content == null || content === '') return null;
    const parts = content.split(/\*\*(.+?)\*\*/g);
    return (
        <span className={`whitespace-pre-wrap ${className}`}>
            {parts.map((part, i) =>
                i % 2 === 1 ? <strong key={i}>{part}</strong> : part
            )}
        </span>
    );
}

/**
 * CandidateChatMessage - Renders a single message with different styles based on type.
 */
export function CandidateChatMessage({
    message,
    onButtonClick,
    onRetry,
    onDownloadResume,
    onMultiSelectSubmit,
    isLatest = false,
    showAvatar = true,
    previousMessageType,
}: CandidateChatMessageProps) {
    const isBot = message.role === 'bot';
    const isAfterResumePreview = previousMessageType === 'resume_preview';
    const mbClass =
        showAvatar ? 'mb-4' : isAfterResumePreview ? 'mb-4' : 'mb-1 -mt-3';

    // ==================== LOADING MESSAGE ====================
    if (message.message_type === 'loading' || message.message_type === 'progress') {
        const hasProgress = message.message_data?.percentage !== undefined;
        const progressText = message.content || 'Processing...';

        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div
                    className="flex items-center gap-3 px-4 py-3 rounded-2xl rounded-tl-md"
                    style={{
                        background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                        border: '1px solid rgba(13, 148, 136, 0.15)',
                    }}
                >
                    {/* Spinner */}
                    <div className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />

                    {/* Text */}
                    <div className="flex-1">
                        <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                            {progressText}
                        </p>

                        {/* Progress bar */}
                        {hasProgress && (
                            <div className="mt-2 h-1.5 rounded-full bg-neutral-200 overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all duration-300"
                                    style={{
                                        width: `${message.message_data!.percentage}%`,
                                        background: 'linear-gradient(90deg, #0D9488 0%, #7C3AED 100%)',
                                    }}
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    // ==================== ERROR MESSAGE ====================
    if (message.message_type === 'error') {
        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md mb-2"
                        style={{
                            background: 'rgba(239, 68, 68, 0.05)',
                            border: '1px solid rgba(239, 68, 68, 0.2)',
                        }}
                    >
                        <p className="text-sm" style={{ color: 'var(--status-closed)' }}>
                            <BotContent content={message.content} />
                        </p>
                    </div>

                    {isLatest && onRetry && (
                        <div className="flex gap-2">
                            <button
                                onClick={onRetry}
                                className="px-4 py-2 rounded-xl text-xs font-medium text-white shadow-sm transition-all hover:scale-105 active:scale-95"
                                style={{ background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }}
                            >
                                🔄 Try Again
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // ==================== RESUME PREVIEW ====================
    if (message.message_type === 'resume_preview') {
        const resumeData = message.message_data?.resume_data || {};
        const summary = message.message_data?.summary || {};
        const resumeId = message.message_data?.resume_id;

        return (
            <div className={`flex items-start gap-3 mb-8 animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-md">
                    <p className="text-sm mb-3" style={{ color: 'var(--neutral-dark)' }}>
                        <BotContent content={message.content} />
                    </p>

                    {/* Resume Preview Card – extra mb-8 so "Would you like to save?" never overlaps */}
                    <div
                        className="rounded-2xl overflow-hidden"
                        style={{
                            background: 'white',
                            border: '1px solid var(--neutral-border)',
                            boxShadow: '0 4px 20px rgba(13, 148, 136, 0.08)',
                        }}
                    >
                        {/* Header */}
                        <div
                            className="px-5 py-4 flex items-center gap-3"
                            style={{
                                background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%)',
                            }}
                        >
                            <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center">
                                <FileText className="w-5 h-5 text-teal-600" />
                            </div>
                            <div>
                                <h3 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
                                    {summary.name ?? summary.full_name ?? resumeData.sections?.personal_info?.full_name ?? 'Your Resume'}
                                </h3>
                                <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                                    {summary.role || resumeData.meta?.role_name || 'Resume Ready'}
                                </p>
                            </div>
                        </div>

                        {/* Summary */}
                        {summary.fields_count && (
                            <div className="px-5 py-4 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
                                <div className="flex items-center justify-between text-sm">
                                    <span style={{ color: 'var(--neutral-gray)' }}>Fields completed</span>
                                    <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
                                        {summary.fields_count} fields
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Hint: save adds to history for full preview */}
                        <div className="px-5 py-3 border-t" style={{ borderColor: 'var(--neutral-border)', background: 'rgba(0,0,0,0.02)' }}>
                            <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                                Save to add this resume to your history — then preview or download it anytime from Resume History.
                            </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="px-5 py-4 flex gap-3 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
                            {resumeId && onDownloadResume && (
                                <button
                                    onClick={() => onDownloadResume(resumeId)}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium flex items-center justify-center gap-2 btn-glass"
                                    style={{ color: 'var(--neutral-dark)' }}
                                >
                                    <Download className="w-4 h-4" />
                                    Download PDF
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // ==================== BOOLEAN (YES/NO) MESSAGE ====================
    if (message.message_type === 'boolean') {
        const buttons: CandidateChatButton[] = [
            { id: 'yes', label: 'Yes', variant: 'primary' },
            { id: 'no', label: 'No', variant: 'secondary' },
        ];

        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md"
                        style={{
                            background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                            border: '1px solid rgba(13, 148, 136, 0.1)',
                        }}
                    >
                        <p className="text-sm" style={{ color: 'var(--neutral-dark)' }}>
                            <BotContent content={message.content} />
                        </p>
                    </div>

                    {isLatest && onButtonClick && (
                        <div className="flex gap-2 mt-3">
                            {buttons.map((btn) => (
                                <button
                                    key={btn.id}
                                    onClick={() => onButtonClick(btn)}
                                    className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all hover:scale-105 active:scale-95 ${btn.variant === 'primary'
                                            ? 'text-white shadow-sm'
                                            : 'btn-glass border border-neutral-200'
                                        }`}
                                    style={
                                        btn.variant === 'primary'
                                            ? { background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }
                                            : { color: 'var(--neutral-dark)' }
                                    }
                                >
                                    {btn.id === 'yes' ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                                    {btn.label}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // ==================== MULTI_SELECT (e.g. skills, languages: suggestion buttons + Custom) ====================
    if (message.message_type === 'multi_select') {
        const questionKey = (message.message_data?.question_key as string) || '';
        const rawOptions = message.message_data?.options;
        const options: string[] = Array.isArray(rawOptions)
            ? rawOptions.map((o: unknown) =>
                typeof o === 'string' ? o : (o && typeof o === 'object' && 'label' in o ? String((o as { label?: string }).label) : (o as { id?: string }).id ? String((o as { id: string }).id) : String(o))
            )
            : typeof rawOptions === 'object' && rawOptions !== null
                ? (Object.values(rawOptions) as string[])
                : [];
        return (
            <MultiSelectMessage
                message={message}
                questionKey={questionKey}
                options={options}
                isLatest={isLatest}
                showAvatar={showAvatar}
                mbClass={mbClass}
                onMultiSelectSubmit={onMultiSelectSubmit}
            />
        );
    }

    // ==================== BUTTONS MESSAGE ====================
    if (message.message_type === 'buttons' || message.message_type === 'select') {
        const rawButtons = (message.message_data?.buttons || message.message_data?.options || []) as Array<string | { id?: string; value?: string; label: string; variant?: 'primary' | 'secondary' | 'outline' }>;
        const buttons: CandidateChatButton[] = rawButtons.map((raw) => {
            if (typeof raw === 'string') {
                return { id: raw, label: raw };
            }
            const btn = raw;
            return {
                id: btn.id ?? btn.value ?? btn.label,
                label: btn.label ?? String(btn.id ?? btn.value ?? ''),
                ...(btn.variant && { variant: btn.variant }),
            };
        });

        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 min-w-0 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md"
                        style={{
                            background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                            border: '1px solid rgba(13, 148, 136, 0.1)',
                        }}
                    >
                        <p className="text-sm" style={{ color: 'var(--neutral-dark)' }}>
                            <BotContent content={message.content} />
                        </p>
                    </div>

                    {buttons.length > 0 && isLatest && onButtonClick && (
                        <div className="flex flex-wrap gap-2 sm:gap-3 mt-3">
                            {buttons.map((btn) => (
                                <button
                                    key={btn.id}
                                    onClick={() => onButtonClick(btn)}
                                    className={`min-h-[44px] px-4 py-2.5 sm:py-2 rounded-xl text-sm font-medium transition-all hover:scale-105 active:scale-95 text-left ${btn.variant === 'primary'
                                            ? 'text-white shadow-sm'
                                            : 'btn-glass border border-neutral-200/80 hover:border-teal-300 hover:bg-teal-50/50'
                                        }`}
                                    style={
                                        btn.variant === 'primary'
                                            ? { background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }
                                            : { color: 'var(--neutral-dark)' }
                                    }
                                >
                                    {btn.label}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // ==================== INPUT PROMPTS ====================
    if (
        message.message_type === 'input_text' ||
        message.message_type === 'input_textarea' ||
        message.message_type === 'input_number' ||
        message.message_type === 'input_date' ||
        message.message_type === 'input_file'
    ) {
        const InputIcon =
            message.message_type === 'input_file' ? Upload : FileText;

        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md"
                        style={{
                            background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                            border: '1px solid rgba(13, 148, 136, 0.1)',
                        }}
                    >
                        <p className="text-sm" style={{ color: 'var(--neutral-dark)' }}>
                            <BotContent content={message.content} />
                        </p>
                    </div>

                    {/* Hint for input type */}
                    {isLatest && (
                        <div className="flex items-center gap-2 mt-2 text-xs" style={{ color: 'var(--neutral-gray)' }}>
                            <InputIcon className="w-3.5 h-3.5" />
                            <span>
                                {message.message_type === 'input_file'
                                    ? 'Upload a file below'
                                    : 'Type your answer below'}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // ==================== BOT TEXT MESSAGE ====================
    if (isBot) {
        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md"
                        style={{
                            background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                            border: '1px solid rgba(13, 148, 136, 0.1)',
                        }}
                    >
                        <p className="text-sm" style={{ color: 'var(--neutral-dark)' }}>
                            <BotContent content={message.content} />
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // ==================== USER MESSAGE ====================
    return (
        <div className="flex items-start gap-3 mb-4 justify-end animate-fade-in">
            <div
                className="max-w-md px-4 py-3 rounded-2xl rounded-tr-md"
                style={{
                    background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                    boxShadow: '0 4px 15px rgba(13, 148, 136, 0.2)',
                }}
            >
                <p className="text-sm text-white whitespace-pre-wrap">{message.content}</p>
            </div>
        </div>
    );
}

// ==================== MULTI_SELECT MESSAGE (skills etc.: suggestion buttons + Custom) ====================

function MultiSelectMessage({
    message,
    questionKey,
    options,
    isLatest,
    showAvatar,
    mbClass,
    onMultiSelectSubmit,
}: {
    message: CandidateChatMessageType;
    questionKey: string;
    options: string[];
    isLatest: boolean;
    showAvatar: boolean;
    mbClass: string;
    onMultiSelectSubmit?: (questionKey: string, values: string[]) => void;
}) {
    const [selected, setSelected] = useState<string[]>([]);
    const [customInput, setCustomInput] = useState('');

    const toggle = useCallback((option: string) => {
        setSelected((prev) =>
            prev.includes(option) ? prev.filter((s) => s !== option) : [...prev, option]
        );
    }, []);

    const addCustom = useCallback(() => {
        const val = customInput.trim();
        if (val && !selected.includes(val)) {
            setSelected((prev) => [...prev, val]);
            setCustomInput('');
        }
    }, [customInput, selected]);

    const handleDone = useCallback(() => {
        if (selected.length === 0) return;
        onMultiSelectSubmit?.(questionKey, selected);
    }, [questionKey, selected, onMultiSelectSubmit]);

    return (
        <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
            {showAvatar ? <BotAvatar /> : <div className="w-9" />}
            <div className="flex-1 min-w-0 max-w-lg">
                <div
                    className="px-4 py-3 rounded-2xl rounded-tl-md"
                    style={{
                        background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
                        border: '1px solid rgba(13, 148, 136, 0.1)',
                    }}
                >
                    <p className="text-sm" style={{ color: 'var(--neutral-dark)' }}>
                        <BotContent content={message.content} />
                    </p>
                </div>

                {isLatest && (
                    <div className="mt-3 space-y-3">
                        {/* Suggestion buttons (e.g. languages, skills) */}
                        {options.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                                {options.map((opt) => (
                                    <button
                                        key={opt}
                                        type="button"
                                        onClick={() => toggle(opt)}
                                        className="px-3 py-2 rounded-xl text-sm font-medium transition-all border"
                                        style={{
                                            borderColor: selected.includes(opt)
                                                ? 'var(--teal-500, #0D9488)'
                                                : 'var(--neutral-border)',
                                            background: selected.includes(opt)
                                                ? 'rgba(13, 148, 136, 0.12)'
                                                : 'transparent',
                                            color: selected.includes(opt) ? 'var(--text-primary)' : 'var(--neutral-gray)',
                                        }}
                                    >
                                        {opt}
                                    </button>
                                ))}
                            </div>
                        )}
                        {/* Custom: type your own + Add */}
                        <div className="flex flex-wrap items-center gap-2">
                            <input
                                type="text"
                                value={customInput}
                                onChange={(e) => setCustomInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCustom())}
                                placeholder="Or type your own and add"
                                className="flex-1 min-w-[140px] px-3 py-2 rounded-xl text-sm border border-[var(--neutral-border)] bg-white"
                            />
                            <button
                                type="button"
                                onClick={addCustom}
                                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium btn-glass border border-[var(--neutral-border)]"
                            >
                                <Plus className="w-4 h-4" />
                                Custom
                            </button>
                        </div>
                        {/* Selected summary + Done */}
                        {selected.length > 0 && (
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                                    Selected: {selected.join(', ')}
                                </span>
                                <button
                                    type="button"
                                    onClick={handleDone}
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white shadow-sm"
                                    style={{ background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }}
                                >
                                    <Check className="w-4 h-4" />
                                    Done
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// ==================== BOT AVATAR COMPONENT ====================

function BotAvatar() {
    return (
        <div
            className="flex-shrink-0 w-9 h-9 rounded-xl overflow-hidden"
            style={{
                background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                padding: '2px',
            }}
        >
            <div className="w-full h-full rounded-[9px] overflow-hidden bg-white flex items-center justify-center">
                <Image
                    src="/aivue-chatbot.png"
                    alt="AIVI"
                    width={32}
                    height={32}
                    className="object-cover"
                />
            </div>
        </div>
    );
}
