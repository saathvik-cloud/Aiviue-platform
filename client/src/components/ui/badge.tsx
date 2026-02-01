import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary/10 text-primary border border-primary/20',
        secondary: 'bg-neutral-light text-neutral-gray border border-neutral-border',
        published: 'bg-status-published/10 text-green-700 border border-status-published/30',
        draft: 'bg-status-draft/10 text-amber-700 border border-status-draft/30',
        closed: 'bg-status-closed/10 text-red-700 border border-status-closed/30',
        pending: 'bg-status-pending/10 text-blue-700 border border-status-pending/30',
        accent: 'bg-accent/10 text-accent-dark border border-accent/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

// Helper to get badge variant from job status
export function getStatusVariant(status: string): BadgeProps['variant'] {
  switch (status) {
    case 'published':
      return 'published';
    case 'draft':
      return 'draft';
    case 'closed':
      return 'closed';
    case 'pending':
    case 'processing':
      return 'pending';
    default:
      return 'secondary';
  }
}

export { Badge, badgeVariants };
