'use client';

/**
 * CandidateChatHistory - Chat session history sidebar.
 *
 * Features:
 * - List of past resume building sessions
 * - Session status indicators (active/completed)
 * - Delete session functionality
 * - Load more pagination
 * - Empty state
 */

import type { CandidateChatSession } from '@/types';
import { ArrowLeft, FileText, Loader2, MoreVertical, Trash2 } from 'lucide-react';
import { useState } from 'react';

interface CandidateChatHistoryProps {
    sessions: CandidateChatSession[];
    isLoading?: boolean;
    hasMore?: boolean;
    onSelectSession: (sessionId: string) => void;
    onDeleteSession: (sessionId: string) => void;
    onLoadMore: () => void;
    onBack: () => void;
}

export function CandidateChatHistory({
    sessions,
    isLoading = false,
    hasMore = false,
    onSelectSession,
    onDeleteSession,
    onLoadMore,
    onBack,
}: CandidateChatHistoryProps) {
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
    };

    const getStatusBadge = (status: string) => {
        const config: Record<string, { bg: string; text: string; label: string }> = {
            active: { bg: 'rgba(245, 158, 11, 0.1)', text: '#F59E0B', label: 'In Progress' },
            completed: { bg: 'rgba(16, 185, 129, 0.1)', text: '#10B981', label: 'Completed' },
            abandoned: { bg: 'rgba(107, 114, 128, 0.1)', text: '#6B7280', label: 'Abandoned' },
        };
        const { bg, text, label } = config[status] || config.active;
        return (
            <span
                className="px-2 py-0.5 rounded-full text-xs font-medium"
                style={{ background: bg, color: text }}
            >
                {label}
            </span>
        );
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center gap-3 px-5 py-4 border-b" style={{ borderColor: 'var(--neutral-border)' }}>
                <button
                    onClick={onBack}
                    className="p-2 rounded-lg hover:bg-neutral-100 transition-colors"
                >
                    <ArrowLeft className="w-5 h-5" style={{ color: 'var(--neutral-dark)' }} />
                </button>
                <h3 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
                    Resume History
                </h3>
            </div>

            {/* Sessions List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {isLoading && sessions.length === 0 ? (
                    <div className="flex items-center justify-center h-32">
                        <Loader2 className="w-6 h-6 animate-spin text-teal-500" />
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="text-center py-10">
                        <div className="w-14 h-14 rounded-2xl bg-neutral-100 flex items-center justify-center mx-auto mb-3">
                            <FileText className="w-6 h-6 text-neutral-400" />
                        </div>
                        <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                            No resume sessions yet
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--neutral-gray)' }}>
                            Start building your first resume with AIVI
                        </p>
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            className="group relative rounded-xl border transition-all hover:border-teal-200 hover:bg-teal-50/50 cursor-pointer"
                            style={{ borderColor: 'var(--neutral-border)', background: 'white' }}
                            onClick={() => onSelectSession(session.id)}
                        >
                            <div className="p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-teal-500 flex-shrink-0" />
                                            <h4
                                                className="text-sm font-medium truncate"
                                                style={{ color: 'var(--text-primary)' }}
                                            >
                                                {session.title || `Resume - ${formatDate(session.created_at)}`}
                                            </h4>
                                        </div>

                                        <div className="flex items-center gap-3 mt-2">
                                            {getStatusBadge(session.session_status)}
                                            <span className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                                                {formatDate(session.updated_at)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Actions Menu */}
                                    <div className="relative">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setMenuOpenId(menuOpenId === session.id ? null : session.id);
                                            }}
                                            className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-neutral-100 transition-all"
                                        >
                                            <MoreVertical className="w-4 h-4" style={{ color: 'var(--neutral-gray)' }} />
                                        </button>

                                        {menuOpenId === session.id && (
                                            <div
                                                className="absolute right-0 top-8 w-40 py-1 rounded-lg shadow-lg border z-10"
                                                style={{ background: 'white', borderColor: 'var(--neutral-border)' }}
                                            >
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onDeleteSession(session.id);
                                                        setMenuOpenId(null);
                                                    }}
                                                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-red-50 text-red-600"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                    Delete
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}

                {/* Load More */}
                {hasMore && (
                    <button
                        onClick={onLoadMore}
                        disabled={isLoading}
                        className="w-full py-3 rounded-xl text-sm font-medium transition-all hover:bg-neutral-100 disabled:opacity-50"
                        style={{ color: 'var(--neutral-gray)' }}
                    >
                        {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                        ) : (
                            'Load more'
                        )}
                    </button>
                )}
            </div>
        </div>
    );
}
