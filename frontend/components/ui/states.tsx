'use client';

import { AlertCircle, Loader2 } from 'lucide-react';
import * as React from 'react';

import { cn } from '@/lib/utils';

export function LoadingState({
  className,
  height = 200,
  label = '加载中...',
}: {
  className?: string;
  height?: number;
  label?: string;
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-center text-zinc-500 text-sm gap-2',
        className,
      )}
      style={{ minHeight: height }}
    >
      <Loader2 className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

export function ErrorState({
  className,
  height = 200,
  error,
}: {
  className?: string;
  height?: number;
  error: unknown;
}) {
  const msg =
    error instanceof Error ? error.message : typeof error === 'string' ? error : '请求失败';
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-red-400 text-sm gap-2 p-4',
        className,
      )}
      style={{ minHeight: height }}
    >
      <AlertCircle className="h-5 w-5" />
      <span className="font-medium">加载失败</span>
      <span className="text-xs text-red-400/80 max-w-md text-center">{msg}</span>
      <span className="text-xs text-zinc-500 mt-1">检查后端是否在运行 (localhost:8000)</span>
    </div>
  );
}

export function EmptyState({
  className,
  height = 200,
  message,
  hint,
}: {
  className?: string;
  height?: number;
  message: string;
  hint?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-zinc-500 text-sm gap-2 p-4 text-center',
        className,
      )}
      style={{ minHeight: height }}
    >
      <span>{message}</span>
      {hint && <div className="text-xs text-zinc-600">{hint}</div>}
    </div>
  );
}

/** Helper hook return: { loading, error, empty }. */
export function useDataState<T>(data: T | undefined, error: unknown, isEmpty?: (d: T) => boolean) {
  const loading = !data && !error;
  const isErr = !!error;
  const empty = !!data && (isEmpty ? isEmpty(data) : Array.isArray(data) ? data.length === 0 : false);
  return { loading, isErr, empty };
}
