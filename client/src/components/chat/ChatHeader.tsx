'use client';

import { CheckCircle, History, Plus, Wifi, X } from 'lucide-react';
import Image from 'next/image';

interface ChatHeaderProps {
    title?: string;
    /** When true, show green "Connected"; when false, show "Connecting..." with pulse (session not ready yet). */
    sessionReady?: boolean;
    onNewChat: () => void;
    onToggleHistory: () => void;
    onClose?: () => void;
    showHistoryButton?: boolean;
}

/**
 * ChatHeader - Top bar with AIVI branding, connection status, new chat, and history buttons.
 * Status: "Connecting..." (animated) until session is ready, then "Connected" (green).
 */
export function ChatHeader({
    title = 'AIVI Assistant',
    sessionReady = false,
    onNewChat,
    onToggleHistory,
    onClose,
    showHistoryButton = true,
}: ChatHeaderProps) {
    const status = sessionReady
        ? { color: '#10B981', icon: CheckCircle, text: 'Connected', animate: false as const }
        : { color: 'var(--status-draft)', icon: Wifi, text: 'Connecting...', animate: true as const };
    const StatusIcon = status.icon;

    return (
        <div className="chat-header flex items-center justify-between px-5 py-4 border-b"
            style={{
                background: 'rgba(255, 255, 255, 0.3)',
                borderColor: 'rgba(124, 58, 237, 0.08)'
            }}
        >
            {/* Left: AIVI Avatar + Title + Status */}
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div
                        className="w-11 h-11 rounded-xl overflow-hidden shadow-lg"
                        style={{
                            background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)',
                            padding: '2px'
                        }}
                    >
                        <div className="w-full h-full rounded-[10px] overflow-hidden bg-white flex items-center justify-center">
                            <Image
                                src="/aivue-chatbot.png"
                                alt="AIVI"
                                width={40}
                                height={40}
                                className="object-cover"
                            />
                        </div>
                    </div>
                    {/* Status indicator: green when connected, pulse when connecting */}
                    <div
                        className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white ${!sessionReady ? 'animate-pulse' : ''}`}
                        style={{ backgroundColor: sessionReady ? 'var(--status-published)' : 'var(--status-draft)' }}
                    />
                </div>
                <div>
                    <h2 className="text-base font-semibold gradient-text">{title}</h2>
                    <div className="flex items-center gap-1.5 mt-0.5">
                        <StatusIcon
                            className={`w-3 h-3 ${status.animate ? 'animate-pulse' : ''}`}
                            style={{ color: status.color }}
                        />
                        <span className="text-xs" style={{ color: status.color }}>
                            {status.text}
                        </span>
                    </div>
                </div>
            </div>

            {/* Right: Action Buttons */}
            <div className="flex items-center gap-2">
                <button
                    onClick={onNewChat}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium transition-all hover:scale-105"
                    style={{
                        background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)',
                        color: 'white',
                        boxShadow: '0 4px 15px rgba(124, 58, 237, 0.3)'
                    }}
                    title="Start new chat"
                >
                    <Plus className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">New</span>
                </button>

                {showHistoryButton && (
                    <button
                        onClick={onToggleHistory}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium transition-all hover:scale-105 btn-glass"
                        style={{ color: 'var(--neutral-dark)' }}
                        title="Chat history"
                    >
                        <History className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">History</span>
                    </button>
                )}

                {onClose && (
                    <button
                        onClick={onClose}
                        className="p-2 rounded-xl transition-all hover:bg-gray-100"
                        style={{ color: 'var(--neutral-gray)' }}
                        title="Close"
                    >
                        <X className="w-4 h-4" />
                    </button>
                )}
            </div>
        </div>
    );
}
