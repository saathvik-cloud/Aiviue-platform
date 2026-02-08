'use client';

import type { ChatButton, ChatMessage as ChatMessageType } from '@/types';
import { Briefcase, Clock, DollarSign, MapPin, Users } from 'lucide-react';
import Image from 'next/image';
import { QuickReplyButtons } from './QuickReplyButtons';

interface ChatMessageProps {
    message: ChatMessageType;
    onButtonClick?: (button: ChatButton) => void;
    onCreateJob?: (data?: any) => void;
    onEditJob?: (data?: any) => void;
    isLatest?: boolean;
    showAvatar?: boolean;
}

/**
 * ChatMessage - Renders a single message with different styles based on type.
 * Supports: text, buttons, loading, job_preview, error
 */
export function ChatMessage({
    message,
    onButtonClick,
    onCreateJob,
    onEditJob,
    isLatest = false,
    showAvatar = true,
}: ChatMessageProps) {
    const isBot = message.role === 'bot';
    const mbClass = showAvatar ? 'mb-4' : 'mb-1 -mt-3';

    // Loading message - show progress text if available, otherwise typing dots
    if (message.message_type === 'loading') {
        // Check if this is a progress message (has meaningful content, not just "thinking...")
        const isProgressMessage = message.content && 
            !message.content.toLowerCase().includes('thinking') &&
            message.content.length > 5;

        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div
                    className="flex items-center gap-2 px-4 py-3 rounded-2xl rounded-tl-md"
                    style={{
                        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
                        border: '1px solid rgba(124, 58, 237, 0.1)'
                    }}
                >
                    {isProgressMessage ? (
                        <>
                            {/* Animated spinner */}
                            <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                            {/* Progress text */}
                            <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                                {message.content}
                            </p>
                        </>
                    ) : (
                        /* Default typing dots */
                        <div className="flex gap-1 px-1">
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 typing-dot" style={{ animationDelay: '0s' }} />
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 typing-dot" style={{ animationDelay: '0.2s' }} />
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-500 typing-dot" style={{ animationDelay: '0.4s' }} />
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Error message
    if (message.message_type === 'error') {
        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md mb-2"
                        style={{
                            background: 'rgba(239, 68, 68, 0.05)',
                            border: '1px solid rgba(239, 68, 68, 0.2)'
                        }}
                    >
                        <p className="text-sm" style={{ color: 'var(--status-closed)' }}>
                            {message.content}
                        </p>
                    </div>

                    {isLatest && (
                        <div className="flex gap-2">
                            <button
                                onClick={() => onButtonClick?.({ id: 'retry', label: '🔄 Retry', value: 'retry_generation' })}
                                className="px-4 py-2 rounded-xl text-xs font-medium text-white shadow-sm transition-all hover:scale-105 active:scale-95"
                                style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
                            >
                                🔄 Retry AI Generation
                            </button>
                            <button
                                onClick={() => onButtonClick?.({ id: 'edit', label: '✏️ Edit Details', value: 'edit_last_step' })}
                                className="px-4 py-2 rounded-xl text-xs font-medium btn-glass border border-neutral-200 transition-all hover:bg-neutral-50"
                                style={{ color: 'var(--neutral-dark)' }}
                            >
                                ✏️ Edit Details
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Job Preview
    if (message.message_type === 'job_preview') {
        const jobData = (message.message_data?.job_data || {}) as Record<string, string | number | undefined>;
        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <p
                        className="text-sm mb-3 whitespace-pre-wrap"
                        style={{ color: 'var(--neutral-dark)' }}
                    >
                        {message.content}
                    </p>

                    {/* Job Preview Card */}
                    <div
                        className="rounded-2xl overflow-hidden"
                        style={{
                            background: 'white',
                            border: '1px solid var(--neutral-border)',
                            boxShadow: '0 4px 20px rgba(124, 58, 237, 0.08)'
                        }}
                    >
                        {/* Header */}
                        <div
                            className="px-5 py-4"
                            style={{
                                background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)'
                            }}
                        >
                            <h3 className="text-lg font-semibold gradient-text">{jobData.title}</h3>
                            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs" style={{ color: 'var(--neutral-gray)' }}>
                                {jobData.city && (
                                    <span className="flex items-center gap-1">
                                        <MapPin className="w-3.5 h-3.5" />
                                        {[jobData.city, jobData.state, jobData.country].filter(Boolean).join(', ')}
                                    </span>
                                )}
                                {jobData.work_type && (
                                    <span className="flex items-center gap-1">
                                        <Briefcase className="w-3.5 h-3.5" />
                                        {jobData.work_type}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Details */}
                        <div className="px-5 py-4 space-y-3">
                            {(jobData.salary_min || jobData.salary_max) && (
                                <div className="flex items-center gap-2 text-sm">
                                    <DollarSign className="w-4 h-4" style={{ color: 'var(--status-published)' }} />
                                    <span style={{ color: 'var(--neutral-dark)' }}>
                                        {jobData.currency} {formatSalary(Number(jobData.salary_min) || 0)} - {formatSalary(Number(jobData.salary_max) || 0)}
                                    </span>
                                </div>
                            )}
                            {(jobData.experience_min !== undefined || jobData.experience_max !== undefined) && (
                                <div className="flex items-center gap-2 text-sm">
                                    <Clock className="w-4 h-4" style={{ color: 'var(--status-draft)' }} />
                                    <span style={{ color: 'var(--neutral-dark)' }}>
                                        {jobData.experience_min}-{jobData.experience_max} years experience
                                    </span>
                                </div>
                            )}
                            {jobData.openings_count && (
                                <div className="flex items-center gap-2 text-sm">
                                    <Users className="w-4 h-4" style={{ color: 'var(--primary)' }} />
                                    <span style={{ color: 'var(--neutral-dark)' }}>
                                        {jobData.openings_count} opening{jobData.openings_count > 1 ? 's' : ''}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Description Preview */}
                        {jobData.description && (
                            <div className="px-5 py-4 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
                                <p className="text-xs font-medium mb-2" style={{ color: 'var(--neutral-gray)' }}>
                                    Description
                                </p>
                                <p className="text-sm line-clamp-3" style={{ color: 'var(--neutral-dark)' }}>
                                    {jobData.description}
                                </p>
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="px-5 py-4 flex gap-3 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
                            {onEditJob && (
                                <button
                                    onClick={() => onEditJob(jobData)}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium btn-glass"
                                    style={{ color: 'var(--neutral-dark)' }}
                                >
                                    ✏️ Edit
                                </button>
                            )}
                            {onCreateJob && (
                                <button
                                    onClick={() => onCreateJob(jobData)}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white"
                                    style={{
                                        background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)',
                                        boxShadow: '0 4px 15px rgba(124, 58, 237, 0.3)'
                                    }}
                                >
                                    ✅ Create Job
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Bot message with potential buttons
    if (isBot) {
        const buttons = message.message_data?.buttons as ChatButton[] | undefined;

        return (
            <div className={`flex items-start gap-3 ${mbClass} animate-fade-in`}>
                {showAvatar ? <BotAvatar /> : <div className="w-9" />}
                <div className="flex-1 max-w-lg">
                    <div
                        className="px-4 py-3 rounded-2xl rounded-tl-md"
                        style={{
                            background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
                            border: '1px solid rgba(124, 58, 237, 0.1)'
                        }}
                    >
                        <p
                            className="text-sm whitespace-pre-wrap"
                            style={{ color: 'var(--neutral-dark)' }}
                        >
                            {message.content}
                        </p>
                    </div>

                    {/* Show buttons if available and this is the latest message */}
                    {buttons && buttons.length > 0 && isLatest && onButtonClick && (
                        <QuickReplyButtons
                            buttons={buttons}
                            onSelect={onButtonClick}
                        />
                    )}
                </div>
            </div>
        );
    }

    // User message
    return (
        <div className="flex items-start gap-3 mb-4 justify-end animate-fade-in">
            <div
                className="max-w-md px-4 py-3 rounded-2xl rounded-tr-md"
                style={{
                    background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)',
                    boxShadow: '0 4px 15px rgba(124, 58, 237, 0.2)'
                }}
            >
                <p className="text-sm text-white whitespace-pre-wrap">
                    {message.content}
                </p>
            </div>
        </div>
    );
}

// Bot Avatar Component
function BotAvatar() {
    return (
        <div
            className="flex-shrink-0 w-9 h-9 rounded-xl overflow-hidden"
            style={{
                background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)',
                padding: '2px'
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

// Helper function to format salary
function formatSalary(value: number): string {
    if (!value) return '0';
    if (value >= 100000) {
        return `${(value / 100000).toFixed(1)}L`;
    }
    if (value >= 1000) {
        return `${(value / 1000).toFixed(0)}K`;
    }
    return value.toString();
}
