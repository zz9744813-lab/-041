'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Models() {
  const { data: models } = useSWR<any[]>('/api/models', fetcher, { refreshInterval: 60000 });

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">策略模型</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models?.map((m) => (
          <ModelCard key={m.id} model={m} />
        ))}
      </div>
      {(!models || models.length === 0) && (
        <p className="text-zinc-500 text-sm">没有策略模型。需要先在 strategy_models 表插入(策略名固定:trend_breakout / pullback_trend / ma_trend)。</p>
      )}
    </div>
  );
}

function ModelCard({ model }: { model: any }) {
  const { data: stats30 } = useSWR<any>(
    `/api/models/${model.name}/stats?window=LAST_30D`,
    fetcher,
  );
  return (
    <div className="p-4 bg-zinc-900 rounded border border-zinc-800">
      <div className="flex justify-between mb-2">
        <h2 className="font-semibold">{model.name}</h2>
        <span className="text-sm font-mono text-zinc-400">weight={Number(model.weight).toFixed(2)}</span>
      </div>
      <p className="text-xs text-zinc-500 mb-3">{model.description || '—'}</p>
      {stats30 ? (
        <div className="grid grid-cols-3 gap-2 text-sm">
          <Stat label="trades" value={stats30.trade_count} />
          <Stat label="win_rate" value={stats30.win_rate ? `${(Number(stats30.win_rate) * 100).toFixed(1)}%` : '—'} />
          <Stat label="expectancy" value={stats30.expectancy ?? '—'} />
          <Stat label="profit_factor" value={stats30.profit_factor ?? '—'} />
          <Stat label="avg_R" value={stats30.avg_r_multiple ?? '—'} />
          <Stat label="quality" value={stats30.sample_quality} highlight={stats30.sample_quality} />
        </div>
      ) : (
        <p className="text-xs text-zinc-500">尚无统计</p>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: any; highlight?: string }) {
  let cls = 'text-zinc-100';
  if (highlight === 'INSUFFICIENT') cls = 'text-red-400';
  else if (highlight === 'LOW') cls = 'text-yellow-400';
  else if (highlight === 'GOOD') cls = 'text-green-400';
  return (
    <div className="bg-zinc-950 p-2 rounded">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={`font-mono mt-1 ${cls}`}>{value}</div>
    </div>
  );
}
