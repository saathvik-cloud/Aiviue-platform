'use client';

import { History, Plus, X } from 'lucide-react';
import Image from 'next/image';

interface ChatHeaderProps {
    title?: string;
    onNewChat: () => void;
    onToggleHistory: () => void;
    onClose?: () => void;
    showHistoryButton?: boolean;
}

/**
 * ChatHeader - Top bar with AIVI branding, new chat, and history buttons.
 */
export function ChatHeader({
    title = 'AIVI Assistant',
    onNewChat,
    onToggleHistory,
    onClose,
    showHistoryButton = true,
}: ChatHeaderProps) {
    return (
        <div className="chat-header flex items-center justify-between px-5 py-4 border-b"
            style={{
                background: 'rgba(255, 255, 255, 0.3)',
                borderColor: 'rgba(124, 58, 237, 0.08)'
            }}
        >
            {/* Left: AIVI Avatar + Title */}
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
                    {/* Online indicator */}
                    <div
                        className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white"
                        style={{ backgroundColor: 'var(--status-published)' }}
                    />
                </div>
                <div>
                    <h2 className="text-base font-semibold gradient-text">{title}</h2>
                    <p className="text-[10px] font-medium tracking-wide uppercase opacity-60" style={{ color: 'var(--neutral-dark)' }}>
                        AI Recruiting Expert
                    </p>
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
