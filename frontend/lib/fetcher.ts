/**
 * Shared SWR fetcher.
 *
 * - Throws an Error whose message starts with "<status> " so callers can
 *   detect 4xx/5xx (used by SWR shouldRetryOnError).
 * - Tries to surface the API's `detail` field if present, so the error
 *   panel shows something useful instead of "Internal Server Error".
 */
export const fetcher = async <T>(url: string): Promise<T> => {
  const r = await fetch(url);
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const body = await r.json();
      if (body && typeof body === 'object' && 'detail' in body) {
        detail = String((body as { detail: unknown }).detail);
      }
    } catch {
      // ignore body parse error - we already have statusText
    }
    throw new Error(`${r.status} ${detail}`);
  }
  return r.json() as Promise<T>;
};
