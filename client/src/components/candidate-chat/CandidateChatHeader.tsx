'use client';

/**
 * CandidateChatHeader - Header for the resume builder chat.
 *
 * Features:
 * - Title display with status: session not ready → "Connecting..." (animated); ready → "Connected" (green)
 * - When WebSocket is used: uses connectionStatus (connecting/connected/reconnecting/etc.)
 * - New Chat button, History toggle button
 */

import type { ConnectionStatus } from '@/lib/websocket/candidate-chat-socket';
import { CheckCircle, History, Plus, Wifi, WifiOff } from 'lucide-react';

interface CandidateChatHeaderProps {
    title?: string;
    /** When 'http', status is driven by sessionReady. When 'websocket', uses connectionStatus. */
    transport?: 'http' | 'websocket';
    /** For HTTP: true when session is created and ready (so user can send messages / upload). */
    sessionReady?: boolean;
    connectionStatus?: ConnectionStatus;
    onNewChat: () => void;
    onToggleHistory: () => void;
    showHistoryButton?: boolean;
}

export function CandidateChatHeader({
    title = 'AIVI Resume Builder',
    transport = 'http',
    sessionReady = false,
    connectionStatus = 'disconnected',
    onNewChat,
    onToggleHistory,
    showHistoryButton = true,
}: CandidateChatHeaderProps) {
    const statusConfig: Record<
        ConnectionStatus | 'sessionConnecting',
        { color: string; icon: typeof Wifi; text: string; animate?: boolean }
    > = {
        connecting: { color: 'var(--status-draft)', icon: Wifi, text: 'Connecting...', animate: true },
        connected: { color: '#10B981', icon: Wifi, text: 'Connected' },
        reconnecting: { color: 'var(--status-draft)', icon: Wifi, text: 'Reconnecting...', animate: true },
        disconnected: { color: 'var(--neutral-gray)', icon: WifiOff, text: 'Disconnected' },
        error: { color: 'var(--status-closed)', icon: WifiOff, text: 'Connection Error' },
        sessionConnecting: { color: 'var(--status-draft)', icon: Wifi, text: 'Connecting...', animate: true },
    };

    const status =
        transport === 'http'
            ? sessionReady
                ? { color: '#10B981', icon: CheckCircle, text: 'Connected', animate: false as const }
                : statusConfig.sessionConnecting
            : statusConfig[connectionStatus];
    const StatusIcon = status.icon;
    const isAnimated = 'animate' in status && status.animate;

    return (
        <div
            className="flex items-center justify-between px-3 sm:px-5 py-3 sm:py-4"
            style={{
                background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.08) 0%, rgba(124, 58, 237, 0.05) 100%)',
                borderBottom: '1px solid rgba(13, 148, 136, 0.1)',
            }}
        >
            {/* Left - Title and Status */}
            <div className="flex items-center gap-3">
                {/* Avatar */}
                <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{
                        background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                    }}
                >
                    <span className="text-xl">🤖</span>
                </div>

                <div className="min-w-0 flex-1">
                    <h2 className="text-sm sm:text-base font-semibold truncate" style={{ color: 'var(--text-primary)' }}>
                        {title}
                    </h2>

                    {/* Status: Connecting (animated) until session ready, then Connected (green) */}
                    <div className="flex items-center gap-1.5 mt-0.5">
                        <StatusIcon
                            className={`w-3 h-3 ${isAnimated ? 'animate-pulse' : ''}`}
                            style={{ color: status.color }}
                        />
                        <span className="text-xs" style={{ color: status.color }}>
                            {status.text}
                        </span>
                    </div>
                </div>
            </div>

            {/* Right - Actions */}
            <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                {showHistoryButton && (
                    <button
                        onClick={onToggleHistory}
                        className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2.5 rounded-xl transition-all hover:bg-neutral-100 active:scale-95"
                        title="Chat History"
                    >
                        <History className="w-5 h-5" style={{ color: 'var(--neutral-gray)' }} />
                    </button>
                )}

                <button
                    onClick={onNewChat}
                    className="min-h-[44px] flex items-center gap-2 px-3 sm:px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:scale-105 active:scale-95"
                    style={{
                        background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                    }}
                >
                    <Plus className="w-4 h-4" />
                    <span className="hidden sm:inline">New Resume</span>
                </button>
            </div>
        </div>
    );
}
