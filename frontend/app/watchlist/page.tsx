'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Watchlist() {
  const { data: assets } = useSWR<any[]>('/api/assets?active_only=true', fetcher);
  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">观察池</h1>
      <div className="bg-zinc-900 rounded border border-zinc-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-950">
            <tr>
              <th className="px-3 py-2 text-left">Symbol</th>
              <th className="px-3 py-2 text-left">Name</th>
              <th className="px-3 py-2 text-left">Market</th>
              <th className="px-3 py-2 text-left">Sector</th>
              <th className="px-3 py-2 text-right">Priority</th>
            </tr>
          </thead>
          <tbody>
            {assets?.map((a) => (
              <tr key={a.id} className="border-t border-zinc-800 hover:bg-zinc-950">
                <td className="px-3 py-2 font-mono">{a.symbol}</td>
                <td className="px-3 py-2">{a.name}</td>
                <td className="px-3 py-2 text-zinc-400">{a.market}</td>
                <td className="px-3 py-2 text-zinc-400">{a.sector ?? '—'}</td>
                <td className="px-3 py-2 text-right text-zinc-400">{a.priority}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(!assets || assets.length === 0) && (
        <p className="text-zinc-500 mt-4 text-sm">还没有 Asset。POST /api/assets 创建。</p>
      )}
    </div>
  );
}
