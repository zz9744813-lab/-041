'use client';

import { Download, Eye, X } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import useSWR from 'swr';

import { CandleChart, type ChartMarker, type PriceLine } from '@/components/charts/candle-chart';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogClose, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { Candle, TradeRow } from '@/lib/types';
import { downloadCSV, fmt } from '@/lib/utils';

export default function Positions() {
  const { data: trades } = useSWR<TradeRow[]>('/api/trades?status=OPEN', fetcher, {
    refreshInterval: 30000,
  });
  const [selected, setSelected] = useState<TradeRow | null>(null);
  const [busy, setBusy] = useState(false);

  function exportCsv() {
    if (!trades) return;
    downloadCSV(
      `positions-${new Date().toISOString().slice(0, 10)}.csv`,
      trades.map((t) => ({
        id: t.id,
        symbol: t.symbol,
        model: t.model_name,
        entry_time: t.entry_time,
        entry_price: t.entry_price,
        quantity: t.quantity,
        stop_loss_current: t.stop_loss_current,
        target_1: t.target_1 ?? '',
        target_2: t.target_2 ?? '',
        trailing_activated: t.trailing_stop_activated,
      })),
    );
  }

  async function manualClose(tradeId: number) {
    if (!confirm(`确认手动平仓 trade #${tradeId}？`)) return;
    setBusy(true);
    try {
      const r = await fetch(`/api/trades/${tradeId}/close`, { method: 'POST' });
      if (!r.ok) alert(`平仓失败: ${r.status}`);
      else setSelected(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">持仓</h1>
        <Button variant="outline" size="sm" onClick={exportCsv} className="ml-auto">
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>OPEN 持仓</CardTitle>
          <CardDescription>点击「查看」打开 K 线 + 标注</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>Model</TableHead>
                <TableHead className="text-right">Entry</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">SL</TableHead>
                <TableHead className="text-right">T1</TableHead>
                <TableHead className="text-right">T2</TableHead>
                <TableHead>Trail</TableHead>
                <TableHead>Entry Time</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades?.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono">{t.symbol}</TableCell>
                  <TableCell className="text-zinc-400 text-xs">{t.model_name}</TableCell>
                  <TableCell className="text-right font-mono">{fmt(t.entry_price, 4)}</TableCell>
                  <TableCell className="text-right font-mono">{fmt(t.quantity, 4)}</TableCell>
                  <TableCell className="text-right font-mono">{fmt(t.stop_loss_current, 4)}</TableCell>
                  <TableCell className="text-right font-mono">
                    {t.target_1 ? fmt(t.target_1, 4) : '—'}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {t.target_2 ? fmt(t.target_2, 4) : '—'}
                  </TableCell>
                  <TableCell>
                    {t.trailing_stop_activated ? <Badge variant="success">trail</Badge> : '—'}
                  </TableCell>
                  <TableCell className="text-zinc-500 text-xs">
                    {new Date(t.entry_time).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={() => setSelected(t)}>
                      <Eye className="h-3.5 w-3.5" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {(!trades || trades.length === 0) && (
            <p className="text-zinc-500 p-6 text-sm">没有 OPEN 持仓。</p>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent>
          {selected && <PositionDetail trade={selected} onClose={() => manualClose(selected.id)} busy={busy} />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PositionDetail({
  trade,
  onClose,
  busy,
}: {
  trade: TradeRow;
  onClose: () => void;
  busy: boolean;
}) {
  const { data: candles } = useSWR<Candle[]>(
    `/api/market/candles?symbol=${trade.symbol}&timeframe=1h&limit=200`,
    fetcher,
  );

  const markers: ChartMarker[] = [
    {
      time: trade.entry_time,
      position: 'belowBar',
      color: '#3b82f6',
      shape: 'arrowUp',
      text: `Entry ${fmt(trade.entry_price, 2)}`,
    },
  ];

  const priceLines: PriceLine[] = [
    {
      price: Number(trade.stop_loss_current),
      color: '#ef4444',
      title: 'SL',
      style: 'dashed',
    },
  ];
  if (trade.target_1) {
    priceLines.push({
      price: Number(trade.target_1),
      color: '#22c55e',
      title: 'TP1',
      style: 'dashed',
    });
  }
  if (trade.target_2) {
    priceLines.push({
      price: Number(trade.target_2),
      color: '#22c55e',
      title: 'TP2',
      style: 'dashed',
    });
  }

  return (
    <>
      <DialogHeader>
        <div>
          <DialogTitle>
            {trade.symbol} · 持仓详情
          </DialogTitle>
          <p className="text-xs text-zinc-500 mt-1">
            model={trade.model_name} · entry {new Date(trade.entry_time).toLocaleString()}
          </p>
        </div>
        <DialogClose />
      </DialogHeader>
      <div className="p-4 space-y-4">
        <CandleChart candles={candles ?? []} markers={markers} priceLines={priceLines} height={320} />
        <div className="grid grid-cols-3 gap-3 text-sm">
          <KV label="Entry" value={`$${fmt(trade.entry_price, 4)}`} />
          <KV label="Quantity" value={fmt(trade.quantity, 4)} />
          <KV label="Position $" value={`$${fmt(trade.position_value)}`} />
          <KV label="SL initial" value={`$${fmt(trade.stop_loss_initial, 4)}`} />
          <KV label="SL current" value={`$${fmt(trade.stop_loss_current, 4)}`} />
          <KV
            label="Trailing"
            value={trade.trailing_stop_activated ? '已激活' : '未激活'}
          />
        </div>
        <div className="flex gap-2 justify-end pt-3 border-t border-zinc-800">
          <Link href={`/signals?id=${trade.signal_id}`}>
            <Button variant="outline" size="sm">查看原始信号</Button>
          </Link>
          <Button variant="destructive" size="sm" onClick={onClose} disabled={busy}>
            <X className="h-3.5 w-3.5 mr-1" />
            {busy ? '平仓中...' : '手动平仓'}
          </Button>
        </div>
      </div>
    </>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-zinc-950 p-2 rounded">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="font-mono mt-1">{value}</div>
    </div>
  );
}
