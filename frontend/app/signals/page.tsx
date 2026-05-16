'use client';

import useSWR from 'swr';
import { useState } from 'react';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Signals() {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const url = `/api/signals?limit=200${statusFilter ? `&status=${statusFilter}` : ''}`;
  const { data: signals, mutate } = useSWR<any[]>(url, fetcher, { refreshInterval: 30000 });
  const [busy, setBusy] = useState(false);

  async function runNow() {
    setBusy(true);
    try {
      await fetch('/api/signals/run', { method: 'POST' });
      mutate();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold">信号</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="ml-auto px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm"
        >
          <option value="">全部状态</option>
          {['NEW', 'APPROVED', 'APPROVED_WAITING_ENTRY', 'EXECUTED', 'REJECTED', 'EXPIRED', 'SUPERSEDED'].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <button
          onClick={runNow}
          disabled={busy}
          className="px-3 py-1 bg-zinc-100 text-zinc-900 rounded text-sm disabled:opacity-50"
        >
          {busy ? '运行中...' : '触发信号生成'}
        </button>
      </div>
      <div className="bg-zinc-900 rounded border border-zinc-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-zinc-950">
            <tr>
              <th className="px-3 py-2 text-left">Symbol</th>
              <th className="px-3 py-2 text-left">Type</th>
              <th className="px-3 py-2 text-left">Direction</th>
              <th className="px-3 py-2 text-right">Conf</th>
              <th className="px-3 py-2 text-right">R/R</th>
              <th className="px-3 py-2 text-right">Entry</th>
              <th className="px-3 py-2 text-right">Stop</th>
              <th className="px-3 py-2 text-right">Target</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Reason</th>
            </tr>
          </thead>
          <tbody>
            {signals?.map((s) => (
              <tr key={s.id} className="border-t border-zinc-800 hover:bg-zinc-950">
                <td className="px-3 py-2 font-mono">{s.symbol}</td>
                <td className="px-3 py-2 text-zinc-400">{s.signal_type}</td>
                <td className="px-3 py-2 text-zinc-400">{s.direction}</td>
                <td className="px-3 py-2 text-right">{s.confidence_score}</td>
                <td className="px-3 py-2 text-right">{s.risk_reward_ratio ?? '—'}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {s.entry_low}-{s.entry_high}
                </td>
                <td className="px-3 py-2 text-right font-mono">{s.stop_loss ?? '—'}</td>
                <td className="px-3 py-2 text-right font-mono">{s.target_1 ?? '—'}</td>
                <td className="px-3 py-2 text-zinc-500 text-xs">{s.status}</td>
                <td className="px-3 py-2 text-zinc-500 text-xs max-w-md truncate">{s.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
