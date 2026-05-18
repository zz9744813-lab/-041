'use client';

import dynamic from 'next/dynamic';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, LoadingState } from '@/components/ui/states';
import { fetcher } from '@/lib/fetcher';
import type { ModelSummaryRow } from '@/lib/types';
import { fmt, fmtPct } from '@/lib/utils';

// Lazy-load recharts so it doesn't bloat the bundle of pages that don't use it.
const RMultipleScatter = dynamic(
  () => import('@/components/charts/r-multiple-scatter').then((m) => m.RMultipleScatter),
  { ssr: false, loading: () => <div className="h-[180px] flex items-center justify-center text-zinc-500 text-xs">加载中...</div> },
);

const QUALITY_LABEL: Record<string, string> = {
  INSUFFICIENT: '样本不足', LOW: '样本偏少', ADEQUATE: '样本充足', GOOD: '样本优秀',
};

const DESC_MAP: Record<string, string> = {
  trend_breakout: '识别 20 日突破机会',
  pullback_trend: '趋势中的回调买点',
  ma_trend: '均线趋势跟踪',
};

export default function Models() {
  // Single endpoint replaces 1 + N + N round-trips (model list + per-model
  // stats + per-model recent trades).
  const { data: summary, error } = useSWR<ModelSummaryRow[]>(
    '/api/models/summary?window=LAST_30D&recent_trades_limit=50',
    fetcher,
    { refreshInterval: 120000 },
  );

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">策略模型</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {summary?.map((m) => <ModelCard key={m.name} m={m} />)}
      </div>
      {error ? <p className="text-red-400 text-sm">{String(error.message ?? error)}</p>
        : !summary ? <LoadingState />
        : summary.length === 0 ? <EmptyState message="暂无策略模型" hint="需要在 strategy_models 表插入配置" />
        : null}
    </div>
  );
}

function ModelCard({ m }: { m: ModelSummaryRow }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {m.name}
              <Badge variant={m.is_active ? 'success' : 'muted'}>{m.is_active ? '启用' : '停用'}</Badge>
              <Badge variant="muted">权重 {fmt(m.weight, 2)}</Badge>
              {m.auto_adjust_weight && <Badge variant="info">自动调整</Badge>}
            </CardTitle>
            <CardDescription>{DESC_MAP[m.name] || m.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-xs text-zinc-500">近 30 天表现</div>
        {m.stat ? (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <Stat label="交易次数" value={String(m.stat.trade_count)} />
            <Stat label="胜率" value={m.stat.win_rate ? fmtPct(m.stat.win_rate, 1) : '—'} />
            <Stat label="样本质量" value={QUALITY_LABEL[m.stat.sample_quality] || m.stat.sample_quality} badge={qualityVariant(m.stat.sample_quality)} />
            <Stat label="期望值" value={m.stat.expectancy ? fmt(m.stat.expectancy, 4) : '—'} />
            <Stat label="盈亏比" value={m.stat.profit_factor ? fmt(m.stat.profit_factor, 2) : '—'} />
            <Stat label="平均 R" value={m.stat.avg_r_multiple ? fmt(m.stat.avg_r_multiple, 2) : '—'} />
          </div>
        ) : <p className="text-xs text-zinc-500">暂无统计数据</p>}
        <div className="pt-2 border-t border-zinc-800">
          <div className="text-xs text-zinc-500 mb-2">近期 R 倍数散点图</div>
          <RMultipleScatter trades={m.recent_r_multiples} height={180} />
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, badge }: { label: string; value: string; badge?: 'danger' | 'warning' | 'info' | 'success' | 'muted' }) {
  return (
    <div className="bg-zinc-950 p-2 rounded">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="font-mono mt-1 text-sm">{badge ? <Badge variant={badge}>{value}</Badge> : value}</div>
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
