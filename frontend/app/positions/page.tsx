'use client';

import { Download, Eye, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import useSWR from 'swr';

import { CandleChart, type ChartMarker, type PriceLine } from '@/components/charts/candle-chart';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogClose, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { Candle, TradeRow } from '@/lib/types';
import { downloadCSV, fmt } from '@/lib/utils';

export default function Positions() {
  const { data: trades, error } = useSWR<TradeRow[]>('/api/trades?status=OPEN', fetcher, { refreshInterval: 60000 });
  const [selected, setSelected] = useState<TradeRow | null>(null);
  const [busy, setBusy] = useState(false);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">当前持仓</h1>
        <Button variant="outline" size="sm" onClick={() => trades && downloadCSV(`positions-${new Date().toISOString().slice(0, 10)}.csv`, trades.map((t) => ({ 标的: t.symbol, 策略: t.model_name, 开仓时间: t.entry_time, 开仓价: t.entry_price, 数量: t.quantity, 当前止损: t.stop_loss_current, 目标1: t.target_1 ?? '', 目标2: t.target_2 ?? '', 移动止损: t.trailing_stop_activated })))} disabled={!trades || trades.length === 0} className="ml-auto">
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>未平仓交易</CardTitle>
          <CardDescription>点击「查看」打开 K 线详情</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? <ErrorState error={error} />
            : !trades ? <LoadingState />
            : trades.length === 0
            ? <EmptyState message="暂无持仓" hint="信号通过风控并成交后在此显示" />
            : <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>标的</TableHead>
                    <TableHead>策略</TableHead>
                    <TableHead className="text-right">开仓价</TableHead>
                    <TableHead className="text-right">数量</TableHead>
                    <TableHead className="text-right">止损</TableHead>
                    <TableHead className="text-right">目标1</TableHead>
                    <TableHead className="text-right">目标2</TableHead>
                    <TableHead>移动止损</TableHead>
                    <TableHead>开仓时间</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell className="font-mono">{t.symbol}</TableCell>
                      <TableCell className="text-zinc-400 text-xs">{t.model_name}</TableCell>
                      <TableCell className="text-right font-mono">{fmt(t.entry_price, 4)}</TableCell>
                      <TableCell className="text-right font-mono">{fmt(t.quantity, 4)}</TableCell>
                      <TableCell className="text-right font-mono">{fmt(t.stop_loss_current, 4)}</TableCell>
                      <TableCell className="text-right font-mono">{t.target_1 ? fmt(t.target_1, 4) : '—'}</TableCell>
                      <TableCell className="text-right font-mono">{t.target_2 ? fmt(t.target_2, 4) : '—'}</TableCell>
                      <TableCell>{t.trailing_stop_activated ? <Badge variant="success">已激活</Badge> : '—'}</TableCell>
                      <TableCell className="text-zinc-500 text-xs">{new Date(t.entry_time).toLocaleString()}</TableCell>
                      <TableCell><Button variant="ghost" size="sm" onClick={() => setSelected(t)}><Eye className="h-3.5 w-3.5" /></Button></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
          }
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent>
          {selected && <PositionDetail trade={selected} onClose={async () => { setBusy(true); try { await fetch(`/api/trades/${selected.id}/close`, { method: 'POST' }); setSelected(null); } finally { setBusy(false); } }} busy={busy} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PositionDetail({ trade, onClose, busy }: { trade: TradeRow; onClose: () => void; busy: boolean }) {
  const { data: candles } = useSWR<Candle[]>(`/api/market/candles?symbol=${trade.symbol}&timeframe=1h&limit=200`, fetcher);
  // Memoise so referential identity is stable across re-renders -> CandleChart's
  // useEffect([markers]) won't re-fire on every parent SWR poll.
  const markers = useMemo<ChartMarker[]>(
    () => [{ time: trade.entry_time, position: 'belowBar', color: '#3b82f6', shape: 'arrowUp', text: `开仓 ${fmt(trade.entry_price, 2)}` }],
    [trade.entry_time, trade.entry_price],
  );
  const priceLines = useMemo<PriceLine[]>(() => {
    const arr: PriceLine[] = [{ price: Number(trade.stop_loss_current), color: '#ef4444', title: '止损', style: 'dashed' }];
    if (trade.target_1) arr.push({ price: Number(trade.target_1), color: '#22c55e', title: '目标1', style: 'dashed' });
    if (trade.target_2) arr.push({ price: Number(trade.target_2), color: '#22c55e', title: '目标2', style: 'dotted' });
    return arr;
  }, [trade.stop_loss_current, trade.target_1, trade.target_2]);
  return (
    <>
      <DialogHeader>
        <div>
          <DialogTitle>{trade.symbol} · 持仓详情</DialogTitle>
          <p className="text-xs text-zinc-500 mt-1">策略：{trade.model_name} · 开仓 {new Date(trade.entry_time).toLocaleString()}</p>
        </div>
        <DialogClose />
      </DialogHeader>
      <div className="p-4 space-y-4">
        <CandleChart candles={candles ?? []} markers={markers} priceLines={priceLines} height={320} />
        <div className="grid grid-cols-3 gap-3 text-sm">
          <KV label="开仓价" value={`$${fmt(trade.entry_price, 4)}`} />
          <KV label="数量" value={fmt(trade.quantity, 4)} />
          <KV label="开仓金额" value={`$${fmt(trade.position_value)}`} />
          <KV label="初始止损" value={`$${fmt(trade.stop_loss_initial, 4)}`} />
          <KV label="当前止损" value={`$${fmt(trade.stop_loss_current, 4)}`} />
          <KV label="移动止损" value={trade.trailing_stop_activated ? '已激活' : '未激活'} />
        </div>
        <div className="flex gap-2 justify-end pt-3 border-t border-zinc-800">
          <Button variant="outline" size="sm" onClick={() => window.location.href = `/signals`}>查看原始信号</Button>
          <Button variant="destructive" size="sm" onClick={onClose} disabled={busy}><X className="h-3.5 w-3.5 mr-1" />{busy ? '平仓中...' : '手动平仓'}</Button>
        </div>
      </div>
    </>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return <div className="bg-zinc-950 p-2 rounded"><div className="text-xs text-zinc-500">{label}</div><div className="font-mono mt-1">{value}</div></div>;
}
