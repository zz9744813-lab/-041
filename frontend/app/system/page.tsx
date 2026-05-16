'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function System() {
  const { data: health } = useSWR<any[]>('/api/system/health', fetcher, { refreshInterval: 30000 });
  const { data: freshness } = useSWR<any[]>('/api/system/data-freshness', fetcher, {
    refreshInterval: 60000,
  });
  const { data: llm } = useSWR<any[]>('/api/system/llm-stats', fetcher, { refreshInterval: 60000 });
  const { data: rejects } = useSWR<any[]>('/api/system/reject-reasons', fetcher);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">系统健康度</h1>

      <section className="bg-zinc-900 rounded border border-zinc-800 p-4">
        <h2 className="font-semibold mb-2">最近任务运行</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-zinc-500">
                <th className="text-left">job</th>
                <th className="text-left">started</th>
                <th className="text-left">status</th>
                <th className="text-left">duration</th>
                <th className="text-left">error</th>
              </tr>
            </thead>
            <tbody>
              {health?.slice(0, 30).map((h: any) => {
                const dur =
                  h.started_at && h.finished_at
                    ? `${(
                        (new Date(h.finished_at).getTime() - new Date(h.started_at).getTime()) /
                        1000
                      ).toFixed(1)}s`
                    : '—';
                const cls =
                  h.status === 'SUCCESS'
                    ? 'text-green-400'
                    : h.status === 'FAILED'
                      ? 'text-red-400'
                      : 'text-yellow-400';
                return (
                  <tr key={h.id} className="border-t border-zinc-800">
                    <td className="py-1 font-mono">{h.job_name}</td>
                    <td className="py-1 text-zinc-500 text-xs">
                      {new Date(h.started_at).toLocaleTimeString()}
                    </td>
                    <td className={`py-1 font-mono ${cls}`}>{h.status}</td>
                    <td className="py-1 text-zinc-500">{dur}</td>
                    <td className="py-1 text-red-400 text-xs truncate max-w-md">
                      {h.error_message ?? ''}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-zinc-900 rounded border border-zinc-800 p-4">
        <h2 className="font-semibold mb-2">数据新鲜度</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-zinc-500">
                <th className="text-left">symbol</th>
                <th className="text-left">tf</th>
                <th className="text-left">last bar</th>
                <th className="text-right">skew (min)</th>
                <th className="text-left">status</th>
              </tr>
            </thead>
            <tbody>
              {freshness?.map((f: any, i: number) => (
                <tr key={i} className="border-t border-zinc-800">
                  <td className="py-1 font-mono">{f.symbol}</td>
                  <td className="py-1 text-zinc-400">{f.timeframe}</td>
                  <td className="py-1 text-zinc-500 text-xs">{f.actual ?? '—'}</td>
                  <td className="py-1 text-right">
                    {f.skew_minutes !== null ? f.skew_minutes.toFixed(0) : '—'}
                  </td>
                  <td
                    className={`py-1 font-mono ${
                      f.status === 'STALE' ? 'text-red-400' : 'text-green-400'
                    }`}
                  >
                    {f.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-zinc-900 rounded border border-zinc-800 p-4">
          <h2 className="font-semibold mb-2">LLM 调用统计 (近 7 天)</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-zinc-500">
                <th className="text-left">day</th>
                <th className="text-left">purpose</th>
                <th className="text-right">calls</th>
                <th className="text-right">cached</th>
                <th className="text-right">$</th>
              </tr>
            </thead>
            <tbody>
              {llm?.map((l: any, i: number) => (
                <tr key={i} className="border-t border-zinc-800">
                  <td className="py-1 text-zinc-400">{l.day}</td>
                  <td className="py-1 text-zinc-400">{l.purpose}</td>
                  <td className="py-1 text-right">{l.total}</td>
                  <td className="py-1 text-right">{l.cached_hits}</td>
                  <td className="py-1 text-right font-mono">{Number(l.cost_usd).toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="bg-zinc-900 rounded border border-zinc-800 p-4">
          <h2 className="font-semibold mb-2">风控拒绝 Top 原因</h2>
          <ul className="text-sm space-y-1">
            {rejects?.map((r: any, i: number) => (
              <li key={i} className="flex justify-between">
                <span className="text-zinc-400 text-xs truncate">{r.reason}</span>
                <span className="font-mono text-red-400">{r.n}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
