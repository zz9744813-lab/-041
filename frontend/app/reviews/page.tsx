'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense, useMemo } from 'react';
import useSWR from 'swr';

import { CandleChart, type ChartMarker, type PriceLine } from '@/components/charts/candle-chart';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, LoadingState } from '@/components/ui/states';
import { fetcher } from '@/lib/fetcher';
import type { Candle, ReviewRow, TradeRow } from '@/lib/types';
import { cn, fmt, fmtPct } from '@/lib/utils';

function ReviewsContent() {
  const searchParams = useSearchParams();
  const tradeIdParam = searchParams?.get('trade_id');
  const { data: reviews } = useSWR<ReviewRow[]>('/api/reviews?limit=50', fetcher);
  const focused = useMemo(() => {
    if (!tradeIdParam || !reviews) return null;
    return reviews.find((r) => String(r.trade_id) === tradeIdParam) ?? null;
  }, [tradeIdParam, reviews]);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">交易复盘</h1>
      {focused && <FocusedReview review={focused} />}
      {!reviews ? <LoadingState /> : reviews.length === 0
        ? <EmptyState message="暂无复盘" hint="运行 trade_review_job 后自动生成" />
        : <div className="space-y-3">
            {reviews.map((r) => <ReviewCard key={r.id} review={r} highlighted={r.id === focused?.id} />)}
          </div>
      }
    </div>
  );
}

export default function Reviews() {
  return <Suspense fallback={<div className="max-w-5xl mx-auto p-6 text-sm text-zinc-500">加载中...</div>}><ReviewsContent /></Suspense>;
}

function FocusedReview({ review }: { review: ReviewRow }) {
  const { data: trade } = useSWR<TradeRow>(`/api/trades/${review.trade_id}`, fetcher);
  const { data: candles } = useSWR<Candle[]>(trade ? `/api/market/candles?symbol=${trade.symbol}&timeframe=1h&limit=300` : null, fetcher);
  const markers = useMemo<ChartMarker[]>(() => {
    if (!trade) return [];
    const arr: ChartMarker[] = [
      { time: trade.entry_time, position: 'belowBar', color: '#3b82f6', shape: 'arrowUp', text: `开仓 ${fmt(trade.entry_price, 2)}` },
    ];
    if (trade.exit_time && trade.exit_price) {
      const won = Number(trade.pnl_amount ?? 0) > 0;
      arr.push({ time: trade.exit_time, position: 'aboveBar', color: won ? '#22c55e' : '#ef4444', shape: 'arrowDown', text: `平仓 ${fmt(trade.exit_price, 2)} (${(REASON_LABEL[trade.exit_reason ?? ''] || trade.exit_reason) ?? ''})` });
    }
    return arr;
  }, [trade]);
  const priceLines = useMemo<PriceLine[]>(() => {
    if (!trade) return [];
    const arr: PriceLine[] = [{ price: Number(trade.stop_loss_initial), color: '#ef4444', title: '初始止损', style: 'dashed' }];
    if (Number(trade.stop_loss_current) !== Number(trade.stop_loss_initial)) arr.push({ price: Number(trade.stop_loss_current), color: '#f97316', title: '当前止损', style: 'dashed' });
    if (trade.target_1) arr.push({ price: Number(trade.target_1), color: '#22c55e', title: 'TP1', style: 'dashed' });
    if (trade.target_2) arr.push({ price: Number(trade.target_2), color: '#22c55e', title: 'TP2', style: 'dotted' });
    return arr;
  }, [trade]);
  if (!trade) return <LoadingState />;
  const won = Number(trade.pnl_amount ?? 0) > 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {trade.symbol} · 交易 #{trade.id}
              <Badge variant={won ? 'success' : 'danger'}>{trade.pnl_amount ? `$${fmt(trade.pnl_amount, 2)}` : '—'}</Badge>
              <Badge variant="muted">{trade.realized_r_multiple ? `${fmt(trade.realized_r_multiple, 2)}R` : '—'}</Badge>
            </CardTitle>
            <CardDescription>{trade.model_name} · 开仓 {new Date(trade.entry_time).toLocaleString()}{trade.exit_time && ` · 平仓 ${new Date(trade.exit_time).toLocaleString()}`}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <CandleChart candles={candles ?? []} markers={markers} priceLines={priceLines} height={360} />
        <div className="grid grid-cols-3 gap-2 text-sm">
          <Stat label="入场质量" value={`${review.entry_quality}/5`} />
          <Stat label="出场质量" value={`${review.exit_quality}/5`} />
          <Stat label="风控" value={`${review.risk_control_quality}/5`} />
          <Stat label="盈亏" value={`$${fmt(trade.pnl_amount, 2)}`} tone={won ? 'up' : 'down'} />
          <Stat label="盈亏%" value={fmtPct(trade.pnl_pct)} tone={won ? 'up' : 'down'} />
          <Stat label="退出" value={REASON_LABEL[trade.exit_reason ?? ''] || trade.exit_reason || '—'} />
        </div>
        <div><div className="text-xs font-semibold text-zinc-400 mb-1">摘要</div><p className="text-sm whitespace-pre-wrap text-zinc-200">{review.summary}</p></div>
        {review.what_worked.length > 0 && (
          <div><div className="text-xs font-semibold text-green-400 mb-1">做得好的</div><ul className="list-disc list-inside text-xs text-zinc-300 space-y-0.5">{review.what_worked.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
        )}
        {review.what_failed.length > 0 && (
          <div><div className="text-xs font-semibold text-red-400 mb-1">做得不好的</div><ul className="list-disc list-inside text-xs text-zinc-300 space-y-0.5">{review.what_failed.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
        )}
        {review.model_adjustment_suggestion && (
          <div><div className="text-xs font-semibold text-blue-400 mb-1">模型调整建议</div><p className="text-xs text-zinc-300">{review.model_adjustment_suggestion}</p></div>
        )}
        {review.llm_call_log_id != null && (
          <div className="pt-2 border-t border-zinc-800">
            <a href={`/llm/${review.llm_call_log_id}`} className="text-xs text-blue-400 hover:underline">查看完整 LLM 调用 (prompt / 输入 / 思考 / 原始响应) →</a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ReviewCard({ review, highlighted }: { review: ReviewRow; highlighted: boolean }) {
  return (
    <Card className={cn(highlighted && 'border-blue-700')}>
      <CardHeader className="pb-2">
        <div className="flex justify-between text-sm"><span className="font-mono text-zinc-400">交易 #{review.trade_id}</span><span className="text-zinc-500 text-xs">{new Date(review.created_at).toLocaleString()}</span></div>
      </CardHeader>
      <CardContent>
        <p className="text-sm whitespace-pre-wrap mb-3 text-zinc-200">{review.summary}</p>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <Stat label="入场" value={`${review.entry_quality}/5`} />
          <Stat label="出场" value={`${review.exit_quality}/5`} />
          <Stat label="风控" value={`${review.risk_control_quality}/5`} />
        </div>
      </CardContent>
    </Card>
  );
}

const REASON_LABEL: Record<string, string> = {
  STOP_LOSS: '止损', TAKE_PROFIT_1: '止盈(目标1)', TAKE_PROFIT_2: '止盈(目标2)',
  TRAILING_STOP: '移动止损', AI_RISK_EXIT: 'AI 风控退出', MAX_HOLDING: '持仓超期', MANUAL: '手动平仓',
};

function Stat({ label, value, tone }: { label: string; value: string; tone?: 'up' | 'down' }) {
  return <div className="bg-zinc-950 p-2 rounded"><div className="text-xs text-zinc-500">{label}</div><div className={cn('font-mono mt-1', tone === 'up' && 'text-green-400', tone === 'down' && 'text-red-400')}>{value}</div></div>;
}
