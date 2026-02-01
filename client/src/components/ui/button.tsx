import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-white shadow-sm hover:bg-primary-dark focus-visible:ring-primary',
        secondary:
          'bg-neutral-light text-neutral-dark border border-neutral-border hover:bg-gray-100 focus-visible:ring-neutral-gray',
        accent:
          'bg-accent text-white shadow-sm hover:bg-accent-dark focus-visible:ring-accent',
        destructive:
          'bg-status-closed text-white shadow-sm hover:opacity-90 focus-visible:ring-status-closed',
        outline:
          'border-2 border-neutral-dark bg-transparent text-neutral-dark hover:bg-neutral-dark hover:text-white focus-visible:ring-neutral-dark',
        ghost:
          'text-neutral-gray hover:bg-gray-100 hover:text-neutral-dark focus-visible:ring-neutral-gray',
        link:
          'text-primary underline-offset-4 hover:underline focus-visible:ring-primary',
        success:
          'bg-status-published text-white shadow-sm hover:opacity-90 focus-visible:ring-status-published',
      },
      size: {
        default: 'h-11 px-5 py-2.5',
        sm: 'h-9 px-4 py-2 text-xs',
        lg: 'h-12 px-8 py-3 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, isLoading, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <Loader2 className="animate-spin" />
            {children}
          </>
        ) : (
          children
        )}
      </Comp>
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
