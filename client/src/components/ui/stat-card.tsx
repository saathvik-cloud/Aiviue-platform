import * as React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
  isLoading?: boolean;
  className?: string;
}

export function StatCard({
  label,
  value,
  icon: Icon,
  color,
  bgColor,
  isLoading,
  className,
}: StatCardProps) {
  return (
    <div className={cn('bg-white rounded-2xl p-5 sm:p-6 shadow-sm border border-neutral-border', className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs sm:text-sm font-medium text-neutral-gray">
            {label}
          </p>
          {isLoading ? (
            <div className="h-9 w-12 bg-gray-200 rounded animate-pulse mt-2" />
          ) : (
            <p 
              className="text-2xl sm:text-3xl lg:text-4xl font-bold mt-1 sm:mt-2"
              style={{ color }}
            >
              {value}
            </p>
          )}
        </div>
        <div 
          className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: bgColor }}
        >
          <Icon className="w-5 h-5 sm:w-6 sm:h-6" style={{ color }} />
        </div>
      </div>
    </div>
  );
}
