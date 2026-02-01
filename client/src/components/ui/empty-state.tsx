import * as React from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-4 text-center', className)}>
      <div className="w-16 h-16 rounded-full bg-neutral-light flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-neutral-muted" />
      </div>
      <h3 className="text-base font-semibold text-neutral-dark mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-neutral-gray mb-4 max-w-sm">{description}</p>
      )}
      {action}
    </div>
  );
}
