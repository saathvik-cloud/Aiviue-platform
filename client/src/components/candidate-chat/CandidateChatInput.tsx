'use client';

/**
 * CandidateChatInput - Input component for the resume builder chat.
 *
 * Features:
 * - Text, textarea, number, date input modes
 * - File upload support
 * - Multi-select tags input
 * - Auto-focus and keyboard shortcuts
 * - Character limits and validation
 * - Responsive design
 */

import { Cloud, Paperclip, Send, X } from 'lucide-react';
import { useCallback, useRef, useState } from 'react';

type InputMode = 'text' | 'textarea' | 'number' | 'date' | 'file' | 'disabled';

interface CandidateChatInputProps {
    mode: InputMode;
    placeholder?: string;
    onSend: (value: string, file?: File) => void;
    onFileUpload?: (file: File) => void;
    disabled?: boolean;
    isLoading?: boolean;
    accept?: string; // For file input
    maxFileSizeMb?: number;
    minLength?: number;
    maxLength?: number;
}

export function CandidateChatInput({
    mode = 'text',
    placeholder = 'Type your message...',
    onSend,
    onFileUpload,
    disabled = false,
    isLoading = false,
    accept = '.pdf,.doc,.docx,.png,.jpg,.jpeg',
    maxFileSizeMb = 2,
    minLength,
    maxLength,
}: CandidateChatInputProps) {
    const [value, setValue] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [fileError, setFileError] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const isDisabled = disabled || isLoading || mode === 'disabled';

    // ==================== HANDLERS ====================

    const handleSubmit = useCallback(() => {
        if (isDisabled) return;

        if (mode === 'file' && selectedFile) {
            onFileUpload?.(selectedFile);
            setSelectedFile(null);
            setFileError(null);
            return;
        }

        const trimmedValue = value.trim();
        if (!trimmedValue) return;

        if (minLength && trimmedValue.length < minLength) {
            return; // Don't submit if below minimum
        }

        onSend(trimmedValue, selectedFile || undefined);
        setValue('');
        setSelectedFile(null);
    }, [value, selectedFile, mode, isDisabled, onSend, onFileUpload, minLength]);

    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            // Enter without shift sends (except for textarea which needs shift+enter)
            if (e.key === 'Enter' && !e.shiftKey && mode !== 'textarea') {
                e.preventDefault();
                handleSubmit();
            }
            // For textarea, Ctrl/Cmd+Enter sends
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && mode === 'textarea') {
                e.preventDefault();
                handleSubmit();
            }
        },
        [handleSubmit, mode]
    );

    const handleFileSelect = useCallback(
        (file: File | null) => {
            if (!file) {
                setSelectedFile(null);
                setFileError(null);
                return;
            }

            // Validate file size
            const maxBytes = maxFileSizeMb * 1024 * 1024;
            if (file.size > maxBytes) {
                setFileError(`File must be under ${maxFileSizeMb}MB`);
                return;
            }

            // Validate file type
            if (accept) {
                const allowedTypes = accept.split(',').map((t) => t.trim().toLowerCase());
                const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
                const isAllowed = allowedTypes.some(
                    (type) => type === fileExtension || file.type.includes(type.replace('.', ''))
                );
                if (!isAllowed) {
                    setFileError(`Please upload: ${accept}`);
                    return;
                }
            }

            setSelectedFile(file);
            setFileError(null);
        },
        [accept, maxFileSizeMb]
    );

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragging(false);

            const file = e.dataTransfer.files[0];
            if (file) {
                handleFileSelect(file);
            }
        },
        [handleFileSelect]
    );

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const clearFile = () => {
        setSelectedFile(null);
        setFileError(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // ==================== RENDER ====================

    // File upload mode
    if (mode === 'file') {
        return (
            <div className="p-4 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
                <div
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    className={`relative rounded-xl border-2 border-dashed transition-all ${isDragging
                            ? 'border-teal-400 bg-teal-50'
                            : 'border-neutral-300 hover:border-teal-300'
                        }`}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept={accept}
                        onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        disabled={isDisabled}
                    />

                    <div className="p-6 text-center">
                        {selectedFile ? (
                            <div className="flex items-center justify-center gap-3">
                                <Paperclip className="w-5 h-5 text-teal-500" />
                                <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                                    {selectedFile.name}
                                </span>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        clearFile();
                                    }}
                                    className="p-1 rounded-full hover:bg-neutral-200"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ) : (
                            <>
                                <Cloud className="w-10 h-10 mx-auto mb-2 text-neutral-400" />
                                <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                                    Drop your file here or click to browse
                                </p>
                                <p className="text-xs mt-1" style={{ color: 'var(--neutral-gray)' }}>
                                    Max {maxFileSizeMb}MB • {accept}
                                </p>
                            </>
                        )}
                    </div>
                </div>

                {fileError && (
                    <p className="mt-2 text-xs text-red-500">{fileError}</p>
                )}

                {selectedFile && (
                    <button
                        onClick={handleSubmit}
                        disabled={isDisabled}
                        className="w-full min-h-[44px] mt-3 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                        style={{ background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }}
                    >
                        {isLoading ? 'Uploading...' : 'Upload File'}
                    </button>
                )}
            </div>
        );
    }

    // Textarea mode
    if (mode === 'textarea') {
        const charCount = value.length;
        const isOverLimit = maxLength ? charCount > maxLength : false;
        const isBelowMin = minLength ? charCount < minLength : false;

        return (
            <div className="p-4 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
                <div className="relative">
                    <textarea
                        ref={textareaRef}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder}
                        disabled={isDisabled}
                        rows={3}
                        className="w-full px-4 py-3 pr-12 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-teal-500/30 transition-all"
                        style={{
                            background: 'rgba(246, 239, 214, 0.5)',
                            border: '1px solid var(--neutral-border)',
                            color: 'var(--text-primary)',
                        }}
                    />

                    <button
                        onClick={handleSubmit}
                        disabled={isDisabled || !value.trim() || isBelowMin || isOverLimit}
                        className="absolute bottom-3 right-3 p-2 rounded-lg transition-all hover:scale-110 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
                        style={{
                            background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                        }}
                    >
                        {isLoading ? (
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <Send className="w-4 h-4 text-white" />
                        )}
                    </button>
                </div>

                {/* Character count */}
                {maxLength && (
                    <div className="flex justify-end mt-1">
                        <span
                            className="text-xs"
                            style={{ color: isOverLimit ? 'var(--status-closed)' : 'var(--neutral-gray)' }}
                        >
                            {charCount}/{maxLength}
                        </span>
                    </div>
                )}

                {/* Hint */}
                <p className="text-xs mt-2" style={{ color: 'var(--neutral-gray)' }}>
                    Press Ctrl+Enter to send
                </p>
            </div>
        );
    }

    // Default text/number/date input
    return (
        <div className="p-4 border-t" style={{ borderColor: 'var(--neutral-border)' }}>
            <div className="flex items-center gap-2">
                <div className="relative flex-1">
                    <input
                        type={mode === 'number' ? 'number' : mode === 'date' ? 'date' : 'text'}
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={placeholder}
                        disabled={isDisabled}
                        className="w-full px-4 py-3 pr-12 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 transition-all"
                        style={{
                            background: 'rgba(246, 239, 214, 0.5)',
                            border: '1px solid var(--neutral-border)',
                            color: 'var(--text-primary)',
                        }}
                    />
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={isDisabled || !value.trim()}
                    className="min-h-[44px] min-w-[44px] flex items-center justify-center p-3 rounded-xl transition-all hover:scale-110 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
                    style={{
                        background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)',
                    }}
                >
                    {isLoading ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                        <Send className="w-5 h-5 text-white" />
                    )}
                </button>
            </div>
        </div>
    );
}
