'use client';

import useSWR from 'swr';

import { RMultipleScatter } from '@/components/charts/r-multiple-scatter';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { fetcher } from '@/lib/fetcher';
import type { ModelStatRow, StrategyModelRow, TradeRow } from '@/lib/types';
import { fmt, fmtPct } from '@/lib/utils';

export default function Models() {
  const { data: models } = useSWR<StrategyModelRow[]>('/api/models', fetcher, {
    refreshInterval: 60000,
  });

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">策略模型</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {models?.map((m) => (
          <ModelCard key={m.id} model={m} />
        ))}
      </div>
      {(!models || models.length === 0) && (
        <p className="text-zinc-500 text-sm">
          没有策略模型。需要先在 strategy_models 表插入(策略名固定:trend_breakout / pullback_trend / ma_trend)。
        </p>
      )}
    </div>
  );
}

function qualityVariant(q: string): 'danger' | 'warning' | 'info' | 'success' | 'muted' {
  if (q === 'INSUFFICIENT') return 'danger';
  if (q === 'LOW') return 'warning';
  if (q === 'ADEQUATE') return 'info';
  if (q === 'GOOD') return 'success';
  return 'muted';
}

function ModelCard({ model }: { model: StrategyModelRow }) {
  const { data: stats30 } = useSWR<ModelStatRow>(
    `/api/models/${model.name}/stats?window=LAST_30D`,
    fetcher,
  );
  const { data: trades } = useSWR<TradeRow[]>(
    `/api/models/${model.name}/recent-trades?limit=200`,
    fetcher,
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {model.name}
              <Badge variant={model.is_active ? 'success' : 'muted'}>
                {model.is_active ? 'active' : 'inactive'}
              </Badge>
              <Badge variant="muted">weight {fmt(model.weight, 2)}</Badge>
              {model.auto_adjust_weight && <Badge variant="info">auto</Badge>}
            </CardTitle>
            <CardDescription>{model.description || '—'}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-xs text-zinc-500">LAST_30D 统计</div>
        {stats30 ? (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <Stat label="trades" value={String(stats30.trade_count)} />
            <Stat
              label="win rate"
              value={stats30.win_rate ? fmtPct(stats30.win_rate, 1) : '—'}
            />
            <Stat
              label="quality"
              value={stats30.sample_quality}
              badge={qualityVariant(stats30.sample_quality)}
            />
            <Stat
              label="expectancy"
              value={stats30.expectancy ? fmt(stats30.expectancy, 4) : '—'}
            />
            <Stat
              label="profit factor"
              value={stats30.profit_factor ? fmt(stats30.profit_factor, 2) : '—'}
            />
            <Stat
              label="avg R"
              value={stats30.avg_r_multiple ? fmt(stats30.avg_r_multiple, 2) : '—'}
            />
          </div>
        ) : (
          <p className="text-xs text-zinc-500">尚无统计</p>
        )}
        <div className="pt-2 border-t border-zinc-800">
          <div className="text-xs text-zinc-500 mb-2">近期 R Multiple 散点</div>
          <RMultipleScatter trades={trades ?? []} height={180} />
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  badge,
}: {
  label: string;
  value: string;
  badge?: 'danger' | 'warning' | 'info' | 'success' | 'muted';
}) {
  return (
    <div className="bg-zinc-950 p-2 rounded">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="font-mono mt-1 text-sm">
        {badge ? <Badge variant={badge}>{value}</Badge> : value}
      </div>
    </div>
  );
}
