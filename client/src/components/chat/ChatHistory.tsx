'use client';

import type { ChatSession } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ChevronLeft, Loader2, MessageSquare, Trash2 } from 'lucide-react';

interface ChatHistoryProps {
    sessions: ChatSession[];
    isLoading: boolean;
    hasMore: boolean;
    onSelectSession: (sessionId: string) => void;
    onDeleteSession: (sessionId: string) => void;
    onLoadMore: () => void;
    onBack: () => void;
}

/**
 * ChatHistory - Paginated list of chat sessions.
 * Shown when user clicks "History" button.
 */
export function ChatHistory({
    sessions,
    isLoading,
    hasMore,
    onSelectSession,
    onDeleteSession,
    onLoadMore,
    onBack,
}: ChatHistoryProps) {
    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div
                className="flex items-center gap-3 px-5 py-4 border-b"
                style={{ borderColor: 'var(--neutral-border)' }}
            >
                <button
                    onClick={onBack}
                    className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
                    style={{ color: 'var(--neutral-dark)' }}
                >
                    <ChevronLeft className="w-5 h-5" />
                </button>
                <h2 className="text-base font-semibold" style={{ color: 'var(--neutral-dark)' }}>
                    Chat History
                </h2>
            </div>

            {/* Sessions List */}
            <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-2">
                {isLoading && sessions.length === 0 ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--primary)' }} />
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="text-center py-12">
                        <div
                            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                            style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
                        >
                            <MessageSquare className="w-6 h-6" style={{ color: 'var(--primary)' }} />
                        </div>
                        <p className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                            No chat history yet
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--neutral-gray)' }}>
                            Start a new conversation with AIVI
                        </p>
                    </div>
                ) : (
                    <>
                        {sessions.map((session) => (
                            <div
                                key={session.id}
                                className="group flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all hover:bg-white"
                                style={{
                                    background: 'rgba(255, 255, 255, 0.5)',
                                    border: '1px solid var(--neutral-border)'
                                }}
                                onClick={() => onSelectSession(session.id)}
                            >
                                <div
                                    className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)'
                                    }}
                                >
                                    <MessageSquare className="w-5 h-5" style={{ color: 'var(--primary)' }} />
                                </div>

                                <div className="flex-1 min-w-0">
                                    <p
                                        className="text-sm font-medium truncate"
                                        style={{ color: 'var(--neutral-dark)' }}
                                    >
                                        {session.title || 'Job Creation Chat'}
                                    </p>
                                    <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
                                        {session.message_count} messages • {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
                                    </p>
                                </div>

                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDeleteSession(session.id);
                                    }}
                                    className="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-red-50 transition-all"
                                    style={{ color: 'var(--status-closed)' }}
                                    title="Delete chat"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}

                        {/* Load More */}
                        {hasMore && (
                            <button
                                onClick={onLoadMore}
                                disabled={isLoading}
                                className="w-full py-3 text-sm font-medium rounded-xl transition-all hover:bg-white"
                                style={{
                                    color: 'var(--primary)',
                                    border: '1px dashed var(--neutral-border)'
                                }}
                            >
                                {isLoading ? (
                                    <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                                ) : (
                                    'Load more'
                                )}
                            </button>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
