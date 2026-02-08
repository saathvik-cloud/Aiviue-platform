'use client';

import type { LucideIcon } from 'lucide-react';
import { EmptyState } from './empty-state';
import { SkeletonList } from './skeleton';

export interface LoadingContentProps {
  /** Show skeleton instead of children */
  isLoading: boolean;
  /** When true and not loading, show empty state (or emptyContent) instead of children */
  isEmpty: boolean;
  /** Number of skeleton cards when using default skeleton (default 3) */
  skeletonCount?: number;
  /** Custom skeleton when loading; overrides default SkeletonList */
  renderSkeleton?: React.ReactNode;
  /** Custom empty UI; when set, emptyIcon/title/description/action are ignored */
  emptyContent?: React.ReactNode;
  /** Used when emptyContent is not set */
  emptyIcon?: LucideIcon;
  /** Used when emptyContent is not set */
  emptyTitle?: string;
  /** Used when emptyContent is not set */
  emptyDescription?: string;
  /** Used when emptyContent is not set */
  emptyAction?: React.ReactNode;
  /** Wrapper class for skeleton and empty states */
  className?: string;
  children: React.ReactNode;
}

/**
 * Consolidates loading / empty / content states for list and detail views.
 * Use in layout/containers so loading and empty state handling live in one place.
 */
export function LoadingContent({
  isLoading,
  isEmpty,
  skeletonCount = 3,
  renderSkeleton,
  emptyContent,
  emptyIcon: EmptyIcon,
  emptyTitle,
  emptyDescription,
  emptyAction,
  className,
  children,
}: LoadingContentProps) {
  if (isLoading) {
    return (
      <div className={className}>
        {renderSkeleton ?? <SkeletonList count={skeletonCount} />}
      </div>
    );
  }

  if (isEmpty) {
    if (emptyContent) return <div className={className}>{emptyContent}</div>;
    if (EmptyIcon && emptyTitle) {
      return (
        <div className={className}>
          <EmptyState
            icon={EmptyIcon}
            title={emptyTitle}
            description={emptyDescription}
            action={emptyAction}
          />
        </div>
      );
    }
  }

  return <>{children}</>;
}
