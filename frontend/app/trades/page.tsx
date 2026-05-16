'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Trades() {
  const { data: trades } = useSWR<any[]>('/api/trades?status=CLOSED&limit=100', fetcher, {
    refreshInterval: 60000,
  });

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">历史交易</h1>
      <div className="bg-zinc-900 rounded border border-zinc-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-950">
            <tr>
              <th className="px-3 py-2 text-left">Symbol</th>
              <th className="px-3 py-2 text-left">Model</th>
              <th className="px-3 py-2 text-right">Entry</th>
              <th className="px-3 py-2 text-right">Exit</th>
              <th className="px-3 py-2 text-right">P&L</th>
              <th className="px-3 py-2 text-right">P&L %</th>
              <th className="px-3 py-2 text-right">R Multiple</th>
              <th className="px-3 py-2 text-left">Reason</th>
            </tr>
          </thead>
          <tbody>
            {trades?.map((t) => {
              const pnl = Number(t.pnl_amount ?? 0);
              const cls = pnl > 0 ? 'text-green-400' : 'text-red-400';
              return (
                <tr key={t.id} className="border-t border-zinc-800">
                  <td className="px-3 py-2 font-mono">{t.symbol}</td>
                  <td className="px-3 py-2 text-zinc-400">{t.model_name}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(t.entry_price).toFixed(4)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {t.exit_price ? Number(t.exit_price).toFixed(4) : '—'}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${cls}`}>{pnl.toFixed(2)}</td>
                  <td className={`px-3 py-2 text-right font-mono ${cls}`}>
                    {t.pnl_pct ? `${(Number(t.pnl_pct) * 100).toFixed(2)}%` : '—'}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {t.realized_r_multiple ? Number(t.realized_r_multiple).toFixed(2) : '—'}
                  </td>
                  <td className="px-3 py-2 text-zinc-400 text-xs">{t.exit_reason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
