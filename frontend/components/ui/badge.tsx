import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium font-mono whitespace-nowrap',
  {
    variants: {
      variant: {
        default: 'border-zinc-700 bg-zinc-800 text-zinc-100',
        success: 'border-green-700 bg-green-900/40 text-green-400',
        warning: 'border-yellow-700 bg-yellow-900/30 text-yellow-400',
        danger: 'border-red-700 bg-red-900/40 text-red-400',
        info: 'border-blue-700 bg-blue-900/30 text-blue-400',
        muted: 'border-zinc-800 bg-transparent text-zinc-500',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
