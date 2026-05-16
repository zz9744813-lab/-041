'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

interface PortfolioSnapshot {
  cash: string;
  equity: string;
  total_return_pct: string;
  max_drawdown_pct: string;
  open_positions_count: number;
  consecutive_losses: number;
}

interface RegimeRow {
  regime: string | null;
  notes?: string;
}

export default function Home() {
  const { data: portfolio } = useSWR<PortfolioSnapshot>('/api/portfolio', fetcher, {
    refreshInterval: 30000,
  });
  const { data: regime } = useSWR<RegimeRow>('/api/market/regime', fetcher, {
    refreshInterval: 60000,
  });
  const { data: signals } = useSWR<unknown[]>('/api/signals?limit=10', fetcher, {
    refreshInterval: 30000,
  });

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Mini Hermes Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card label="账户净值" value={portfolio ? `$${Number(portfolio.equity).toFixed(2)}` : '—'} />
        <Card
          label="累计收益"
          value={portfolio ? `${(Number(portfolio.total_return_pct) * 100).toFixed(2)}%` : '—'}
          highlight={portfolio && Number(portfolio.total_return_pct) > 0 ? 'up' : 'down'}
        />
        <Card
          label="最大回撤"
          value={portfolio ? `${(Number(portfolio.max_drawdown_pct) * 100).toFixed(2)}%` : '—'}
          highlight="down"
        />
        <Card label="持仓数" value={portfolio ? String(portfolio.open_positions_count) : '—'} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-zinc-900 rounded border border-zinc-800">
          <div className="text-xs text-zinc-500">市场环境</div>
          <div className="text-lg font-mono mt-2">{regime?.regime ?? '尚未计算'}</div>
          {regime?.notes && <div className="text-xs text-zinc-500 mt-1">{regime.notes}</div>}
        </div>
        <div className="p-4 bg-zinc-900 rounded border border-zinc-800">
          <div className="text-xs text-zinc-500">连续亏损</div>
          <div className="text-lg font-mono mt-2">{portfolio?.consecutive_losses ?? '—'} 笔</div>
          <div className="text-xs text-zinc-500 mt-1">≥3 笔自动减半仓位; ≥5 笔暂停 48h</div>
        </div>
      </div>

      <div className="p-4 bg-zinc-900 rounded border border-zinc-800">
        <div className="text-sm font-semibold mb-2">最近信号</div>
        {!signals || signals.length === 0 ? (
          <p className="text-sm text-zinc-500">暂无信号。运行 `python -m app.scheduler` 或调用 POST /api/signals/run。</p>
        ) : (
          <ul className="text-sm space-y-1">
            {signals.slice(0, 10).map((s: any) => (
              <li key={s.id} className="flex justify-between">
                <span>
                  <span className="font-mono">{s.symbol}</span>{' '}
                  <span className="text-zinc-500">{s.signal_type}</span>{' '}
                  <span className="text-zinc-400">conf={s.confidence_score}</span>
                </span>
                <span className="text-xs text-zinc-500">{s.status}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Card({ label, value, highlight }: { label: string; value: string; highlight?: string }) {
  let cls = 'text-zinc-100';
  if (highlight === 'up') cls = 'text-green-400';
  else if (highlight === 'down') cls = 'text-red-400';
  return (
    <div className="p-4 bg-zinc-900 rounded border border-zinc-800">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={`text-2xl font-bold mt-2 font-mono ${cls}`}>{value}</div>
    </div>
  );
}
