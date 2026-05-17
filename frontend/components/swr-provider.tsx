'use client';
/**
 * Global SWR configuration provider.
 *
 * Tames the polling storm:
 *   - dedupingInterval: collapse identical requests within 5s to one fetch
 *   - focusThrottleInterval: don't re-fetch on every tab switch
 *   - revalidateOnFocus / revalidateOnReconnect: turned off (we'll rely on
 *     each hook's explicit refreshInterval instead)
 *   - keepPreviousData: while a new key loads (e.g. filter change), keep
 *     showing the old data so the UI doesn't flicker through a Loading state
 *   - errorRetryCount: 2 attempts is plenty; was unbounded by default
 */
import type { ReactNode } from 'react';
import { SWRConfig } from 'swr';

import { fetcher } from '@/lib/fetcher';

export function SwrProvider({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        fetcher,
        dedupingInterval: 5000,
        focusThrottleInterval: 30000,
        revalidateOnFocus: false,
        revalidateOnReconnect: false,
        keepPreviousData: true,
        errorRetryCount: 2,
        shouldRetryOnError: (err) => {
          // 4xx are usually our bug, not a transient issue - don't retry
          const m = String(err?.message ?? '').match(/^(\d{3})/);
          if (m) {
            const code = Number(m[1]);
            if (code >= 400 && code < 500) return false;
          }
          return true;
        },
      }}
    >
      {children}
    </SWRConfig>
  );
}
