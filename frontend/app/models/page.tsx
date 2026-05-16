'use client';

import useSWR from 'swr';

import { RMultipleScatter } from '@/components/charts/r-multiple-scatter';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, LoadingState } from '@/components/ui/states';
import { fetcher } from '@/lib/fetcher';
import type { ModelStatRow, StrategyModelRow, TradeRow } from '@/lib/types';
import { fmt, fmtPct } from '@/lib/utils';

const QUALITY_LABEL: Record<string, string> = {
  INSUFFICIENT: '样本不足', LOW: '样本偏少', ADEQUATE: '样本充足', GOOD: '样本优秀',
};

export default function Models() {
  const { data: models } = useSWR<StrategyModelRow[]>('/api/models', fetcher, { refreshInterval: 60000 });

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">策略模型</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {models?.map((m) => <ModelCard key={m.id} model={m} />)}
      </div>
      {!models ? <LoadingState /> : models.length === 0 && <EmptyState message="暂无策略模型" hint="需要在 strategy_models 表插入配置" />}
    </div>
  );
}

function ModelCard({ model }: { model: StrategyModelRow }) {
  const { data: stats30 } = useSWR<ModelStatRow>(`/api/models/${model.name}/stats?window=LAST_30D`, fetcher);
  const { data: trades } = useSWR<TradeRow[]>(`/api/models/${model.name}/recent-trades?limit=200`, fetcher);

  const descMap: Record<string, string> = { trend_breakout: '识别 20 日突破机会', pullback_trend: '趋势中的回调买点', ma_trend: '均线趋势跟踪' };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {model.name}
              <Badge variant={model.is_active ? 'success' : 'muted'}>{model.is_active ? '启用' : '停用'}</Badge>
              <Badge variant="muted">权重 {fmt(model.weight, 2)}</Badge>
              {model.auto_adjust_weight && <Badge variant="info">自动调整</Badge>}
            </CardTitle>
            <CardDescription>{descMap[model.name] || model.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
		<div className="text-xs text-zinc-500">近 30 天表现</div>
        {stats30 ? (
          <div className="grid grid-cols-3 gap-2 text-sm">
            <Stat label="交易次数" value={String(stats30.trade_count)} />
            <Stat label="胜率" value={stats30.win_rate ? fmtPct(stats30.win_rate, 1) : '—'} />
            <Stat label="样本质量" value={QUALITY_LABEL[stats30.sample_quality] || stats30.sample_quality} badge={qualityVariant(stats30.sample_quality)} />
            <Stat label="期望值" value={stats30.expectancy ? fmt(stats30.expectancy, 4) : '—'} />
            <Stat label="盈亏比" value={stats30.profit_factor ? fmt(stats30.profit_factor, 2) : '—'} />
            <Stat label="平均 R" value={stats30.avg_r_multiple ? fmt(stats30.avg_r_multiple, 2) : '—'} />
          </div>
        ) : <p className="text-xs text-zinc-500">暂无统计数据</p>}
        <div className="pt-2 border-t border-zinc-800">
          <div className="text-xs text-zinc-500 mb-2">近期 R 倍数散点图</div>
          <RMultipleScatter trades={trades ?? []} height={180} />
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, badge }: { label: string; value: string; badge?: 'danger' | 'warning' | 'info' | 'success' | 'muted' }) {
  return <div className="bg-zinc-950 p-2 rounded"><div className="text-xs text-zinc-500">{label}</div><div className="font-mono mt-1 text-sm">{badge ? <Badge variant={badge}>{value}</Badge> : value}</div></div>;
}

function qualityVariant(q: string): 'danger' | 'warning' | 'info' | 'success' | 'muted' {
  if (q === 'INSUFFICIENT') return 'danger';
  if (q === 'LOW') return 'warning';
  if (q === 'ADEQUATE') return 'info';
  if (q === 'GOOD') return 'success';
  return 'muted';
}
