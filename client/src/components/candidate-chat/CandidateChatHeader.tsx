'use client';

/**
 * CandidateChatHeader - Header for the resume builder chat.
 *
 * Features:
 * - Title display with status (Ready when HTTP; Connected/Reconnecting/etc. when WebSocket)
 * - New Chat button
 * - History toggle button
 */

import type { ConnectionStatus } from '@/lib/websocket/candidate-chat-socket';
import { CheckCircle, History, Plus, Wifi, WifiOff } from 'lucide-react';

interface CandidateChatHeaderProps {
    title?: string;
    /** When 'http', shows "Ready" (no WebSocket). When 'websocket', uses connectionStatus. */
    transport?: 'http' | 'websocket';
    connectionStatus?: ConnectionStatus;
    onNewChat: () => void;
    onToggleHistory: () => void;
    showHistoryButton?: boolean;
}

export function CandidateChatHeader({
    title = 'AIVI Resume Builder',
    transport = 'http',
    connectionStatus = 'disconnected',
    onNewChat,
    onToggleHistory,
    showHistoryButton = true,
}: CandidateChatHeaderProps) {
    const statusConfig = {
        connecting: { color: 'var(--status-draft)', icon: Wifi, text: 'Connecting...' },
        connected: { color: '#10B981', icon: Wifi, text: 'Connected' },
        reconnecting: { color: 'var(--status-draft)', icon: Wifi, text: 'Reconnecting...' },
        disconnected: { color: 'var(--neutral-gray)', icon: WifiOff, text: 'Disconnected' },
        error: { color: 'var(--status-closed)', icon: WifiOff, text: 'Connection Error' },
    };

    const status =
        transport === 'http'
            ? { color: '#10B981', icon: CheckCircle, text: 'connected' }
            : statusConfig[connectionStatus];
    const StatusIcon = status.icon;

    return (
        <div
            className="flex items-center justify-between px-5 py-4"
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

                <div>
                    <h2 className="text-base font-semibold" style={{ color: 'var(--text-primary)' }}>
                        {title}
                    </h2>

                    {/* Status: "Ready" for HTTP, or WebSocket connection status when transport is websocket */}
                    <div className="flex items-center gap-1.5 mt-0.5">
                        <StatusIcon className="w-3 h-3" style={{ color: status.color }} />
                        <span className="text-xs" style={{ color: status.color }}>
                            {status.text}
                        </span>
                    </div>
                </div>
            </div>

            {/* Right - Actions */}
            <div className="flex items-center gap-2">
                {showHistoryButton && (
                    <button
                        onClick={onToggleHistory}
                        className="p-2.5 rounded-xl transition-all hover:bg-neutral-100 active:scale-95"
                        title="Chat History"
                    >
                        <History className="w-5 h-5" style={{ color: 'var(--neutral-gray)' }} />
                    </button>
                )}

                <button
                    onClick={onNewChat}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all hover:scale-105 active:scale-95"
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
