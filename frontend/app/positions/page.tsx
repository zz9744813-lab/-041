'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Positions() {
  const { data: trades } = useSWR<any[]>('/api/trades?status=OPEN', fetcher, { refreshInterval: 30000 });

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">持仓</h1>
      <div className="bg-zinc-900 rounded border border-zinc-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-950">
            <tr>
              <th className="px-3 py-2 text-left">Symbol</th>
              <th className="px-3 py-2 text-left">Model</th>
              <th className="px-3 py-2 text-right">Entry</th>
              <th className="px-3 py-2 text-right">Qty</th>
              <th className="px-3 py-2 text-right">Stop</th>
              <th className="px-3 py-2 text-right">Target1</th>
              <th className="px-3 py-2 text-right">Target2</th>
              <th className="px-3 py-2 text-left">Trail?</th>
              <th className="px-3 py-2 text-left">Entry Time</th>
            </tr>
          </thead>
          <tbody>
            {trades?.map((t) => (
              <tr key={t.id} className="border-t border-zinc-800">
                <td className="px-3 py-2 font-mono">{t.symbol}</td>
                <td className="px-3 py-2 text-zinc-400">{t.model_name}</td>
                <td className="px-3 py-2 text-right font-mono">{Number(t.entry_price).toFixed(4)}</td>
                <td className="px-3 py-2 text-right font-mono">{Number(t.quantity).toFixed(4)}</td>
                <td className="px-3 py-2 text-right font-mono">{Number(t.stop_loss_current).toFixed(4)}</td>
                <td className="px-3 py-2 text-right font-mono">{t.target_1 ? Number(t.target_1).toFixed(4) : '—'}</td>
                <td className="px-3 py-2 text-right font-mono">{t.target_2 ? Number(t.target_2).toFixed(4) : '—'}</td>
                <td className="px-3 py-2">{t.trailing_stop_activated ? '✓' : ''}</td>
                <td className="px-3 py-2 text-zinc-500 text-xs">{new Date(t.entry_time).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(!trades || trades.length === 0) && (
        <p className="text-zinc-500 mt-4 text-sm">没有 OPEN 持仓。</p>
      )}
    </div>
  );
}
