'use client';
/**
 * Lightweight SSE hook.
 *
 * Subscribes to an EventSource at `url` and accumulates events of the named
 * types into an array. Pass `null` for `url` to pause / unsubscribe.
 *
 * Returns:
 *   events    - chronological list of {type, data} objects
 *   readyState - 'idle' | 'open' | 'closed' | 'error'
 *   error     - last error, if any
 *   reset()   - clears events and forces a fresh subscription
 *
 * The hook listens for an `end` event (sent by our backend) and closes the
 * connection automatically once received.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

export interface SseEvent {
  type: string;
  data: any;
  ts: number;
}

export type SseState = 'idle' | 'open' | 'closed' | 'error';

export function useSse(url: string | null, eventTypes: string[]) {
  const [events, setEvents] = useState<SseEvent[]>([]);
  const [state, setState] = useState<SseState>('idle');
  const [error, setError] = useState<Event | null>(null);
  const sourceRef = useRef<EventSource | null>(null);
  // Snapshot the listened types in a ref so changes to the array reference
  // don't tear down the connection (parents often pass an inline literal).
  const typesRef = useRef<string[]>(eventTypes);
  typesRef.current = eventTypes;

  const reset = useCallback(() => {
    setEvents([]);
    setError(null);
    setState('idle');
    sourceRef.current?.close();
    sourceRef.current = null;
  }, []);

  useEffect(() => {
    if (!url) {
      sourceRef.current?.close();
      sourceRef.current = null;
      setState('idle');
      return;
    }
    const es = new EventSource(url);
    sourceRef.current = es;
    setState('open');

    const handler = (type: string) => (e: MessageEvent) => {
      let parsed: any = e.data;
      try {
        parsed = JSON.parse(e.data);
      } catch {
        // keep raw string
      }
      setEvents((prev) => [...prev, { type, data: parsed, ts: Date.now() }]);
    };

    const listeners: Array<[string, EventListener]> = [];
    typesRef.current.forEach((t) => {
      const fn = handler(t) as unknown as EventListener;
      es.addEventListener(t, fn);
      listeners.push([t, fn]);
    });
    // The `end` event is special: close on receipt.
    const endListener: EventListener = () => {
      setState('closed');
      es.close();
    };
    es.addEventListener('end', endListener);

    es.onerror = (ev) => {
      setError(ev);
      setState('error');
    };

    return () => {
      listeners.forEach(([t, fn]) => es.removeEventListener(t, fn));
      es.removeEventListener('end', endListener);
      es.close();
    };
  }, [url]);

  return { events, state, error, reset };
}
