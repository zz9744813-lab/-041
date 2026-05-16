'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

interface DialogContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DialogContext = React.createContext<DialogContextValue | null>(null);

export function Dialog({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}) {
  return <DialogContext.Provider value={{ open, onOpenChange }}>{children}</DialogContext.Provider>;
}

export function DialogContent({
  children,
  className,
  side = 'right',
}: {
  children: React.ReactNode;
  className?: string;
  side?: 'right' | 'center';
}) {
  const ctx = React.useContext(DialogContext);
  React.useEffect(() => {
    if (!ctx?.open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') ctx.onOpenChange(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [ctx]);

  if (!ctx?.open) return null;

  return (
    <div className="fixed inset-0 z-50 flex" onClick={() => ctx.onOpenChange(false)}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        onClick={(e) => e.stopPropagation()}
        className={cn(
          'relative ml-auto h-full w-full max-w-2xl overflow-y-auto bg-zinc-950 border-l border-zinc-800 shadow-xl',
          side === 'center' &&
            'm-auto h-auto max-h-[90vh] max-w-2xl rounded-lg border border-zinc-800',
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex items-start justify-between border-b border-zinc-800 p-4', className)}>
      {children}
    </div>
  );
}

export function DialogTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <h2 className={cn('text-lg font-semibold text-zinc-100', className)}>{children}</h2>;
}

export function DialogClose() {
  const ctx = React.useContext(DialogContext);
  if (!ctx) return null;
  return (
    <button
      onClick={() => ctx.onOpenChange(false)}
      className="text-zinc-500 hover:text-zinc-100 text-sm px-2 py-1 rounded"
    >
      ✕
    </button>
  );
}
