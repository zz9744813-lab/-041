'use client';

import { Download, FileText } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { TradeRow } from '@/lib/types';
import { cn, downloadCSV, fmt, fmtPct } from '@/lib/utils';

const PAGE_SIZE = 50;

const REASON_LABEL: Record<string, string> = {
  STOP_LOSS: '止损', TAKE_PROFIT_1: '止盈(目标1)', TAKE_PROFIT_2: '止盈(目标2)',
  TRAILING_STOP: '移动止损', AI_RISK_EXIT: 'AI 风控退出', MAX_HOLDING: '持仓超期', MANUAL: '手动平仓',
};

export default function Trades() {
  const [page, setPage] = useState(0);
  const url = `/api/trades?status=CLOSED&limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`;
  const { data: trades, error } = useSWR<TradeRow[]>(url, fetcher, { refreshInterval: 120000 });

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">历史交易</h1>
        <Button
          variant="outline"
          size="sm"
          disabled={!trades || trades.length === 0}
          className="ml-auto"
          onClick={() => trades && downloadCSV(`trades-${new Date().toISOString().slice(0, 10)}.csv`, trades.map((t) => ({
            标的: t.symbol, 策略: t.model_name, 开仓时间: t.entry_time, 开仓价: t.entry_price,
            平仓时间: t.exit_time ?? '', 平仓价: t.exit_price ?? '', 盈亏: t.pnl_amount ?? '',
            '盈亏%': t.pnl_pct ?? '', 'R 倍数': t.realized_r_multiple ?? '',
            退出原因: (REASON_LABEL[t.exit_reason ?? ''] || t.exit_reason) || '',
          })))}
        >
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>已平仓交易</CardTitle>
          <CardDescription>盈亏 / R 倍数 / 退出原因</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? <ErrorState error={error} />
            : !trades ? <LoadingState />
            : trades.length === 0
            ? <EmptyState message="暂无已平仓交易" hint="持仓触发止损/止盈后会出现在这里" />
            : <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>标的</TableHead>
                    <TableHead>策略</TableHead>
                    <TableHead className="text-right">开仓</TableHead>
                    <TableHead className="text-right">平仓</TableHead>
                    <TableHead className="text-right">盈亏</TableHead>
                    <TableHead className="text-right">盈亏%</TableHead>
                    <TableHead className="text-right">R 倍数</TableHead>
                    <TableHead>退出原因</TableHead>
                    <TableHead>信号</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {trades.map((t) => {
                    const pnl = Number(t.pnl_amount ?? 0); const won = pnl > 0;
                    return (
                      <TableRow key={t.id}>
                        <TableCell className="font-mono">{t.symbol}</TableCell>
                        <TableCell className="text-zinc-400 text-xs">{t.model_name}</TableCell>
                        <TableCell className="text-right font-mono">{fmt(t.entry_price, 4)}</TableCell>
                        <TableCell className="text-right font-mono">{t.exit_price ? fmt(t.exit_price, 4) : '—'}</TableCell>
                        <TableCell className={cn('text-right font-mono', won ? 'text-green-400' : 'text-red-400')}>${fmt(t.pnl_amount, 2)}</TableCell>
                        <TableCell className={cn('text-right font-mono', won ? 'text-green-400' : 'text-red-400')}>{fmtPct(t.pnl_pct)}</TableCell>
                        <TableCell className={cn('text-right font-mono', won ? 'text-green-400' : 'text-red-400')}>{t.realized_r_multiple ? `${fmt(t.realized_r_multiple, 2)}R` : '—'}</TableCell>
                        <TableCell>
                          <Badge variant={exitVariant(t.exit_reason)}>{(REASON_LABEL[t.exit_reason ?? ''] || t.exit_reason) || '—'}</Badge>
                        </TableCell>
                        <TableCell>
                          <Link href={`/signals?id=${t.signal_id}`} className="text-xs text-zinc-400 hover:text-blue-400">#{t.signal_id}</Link>
                        </TableCell>
                        <TableCell>
                          <Link href={`/reviews?trade_id=${t.id}`}><Button variant="ghost" size="sm"><FileText className="h-3.5 w-3.5 mr-1" />复盘</Button></Link>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
          }
        </CardContent>
        <div className="flex items-center justify-between p-3 border-t border-zinc-800 text-xs text-zinc-500">
          <div>第 {page + 1} 页 · 每页 {PAGE_SIZE} 条</div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>上一页</Button>
            <Button variant="outline" size="sm" disabled={!trades || trades.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>下一页</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function exitVariant(reason: string | null): 'success' | 'warning' | 'danger' | 'info' | 'muted' {
  if (!reason) return 'muted';
  if (reason.startsWith('TAKE_PROFIT')) return 'success';
  if (reason === 'TRAILING_STOP') return 'info';
  if (reason === 'STOP_LOSS' || reason === 'AI_RISK_EXIT') return 'danger';
  if (reason === 'MAX_HOLDING') return 'warning';
  return 'muted';
}
