'use client';

import { Download, FileText } from 'lucide-react';
import Link from 'next/link';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { TradeRow } from '@/lib/types';
import { cn, downloadCSV, fmt, fmtPct } from '@/lib/utils';

export default function Trades() {
  const { data: trades, error } = useSWR<TradeRow[]>(
    '/api/trades?status=CLOSED&limit=200',
    fetcher,
    { refreshInterval: 60000 },
  );

  function exportCsv() {
    if (!trades) return;
    downloadCSV(
      `trades-${new Date().toISOString().slice(0, 10)}.csv`,
      trades.map((t) => ({
        id: t.id,
        symbol: t.symbol,
        model: t.model_name,
        entry_time: t.entry_time,
        entry_price: t.entry_price,
        exit_time: t.exit_time ?? '',
        exit_price: t.exit_price ?? '',
        pnl_amount: t.pnl_amount ?? '',
        pnl_pct: t.pnl_pct ?? '',
        r_multiple: t.realized_r_multiple ?? '',
        exit_reason: t.exit_reason ?? '',
      })),
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">历史交易</h1>
        <Button variant="outline" size="sm" onClick={exportCsv} className="ml-auto">
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>已平仓交易</CardTitle>
          <CardDescription>P&L / R Multiple / 退出原因</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <ErrorState error={error} />
          ) : !trades ? (
            <LoadingState />
          ) : trades.length === 0 ? (
            <EmptyState message="还没有已平仓交易" hint="持仓触发 SL/TP/MANUAL 后会出现在这里" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Exit</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                  <TableHead className="text-right">P&L %</TableHead>
                  <TableHead className="text-right">R</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((t) => {
                  const pnl = Number(t.pnl_amount ?? 0);
                  const won = pnl > 0;
                  return (
                    <TableRow key={t.id}>
                      <TableCell className="font-mono">{t.symbol}</TableCell>
                      <TableCell className="text-zinc-400 text-xs">{t.model_name}</TableCell>
                      <TableCell className="text-right font-mono">{fmt(t.entry_price, 4)}</TableCell>
                      <TableCell className="text-right font-mono">
                        {t.exit_price ? fmt(t.exit_price, 4) : '—'}
                      </TableCell>
                      <TableCell
                        className={cn(
                          'text-right font-mono',
                          won ? 'text-green-400' : 'text-red-400',
                        )}
                      >
                        ${fmt(t.pnl_amount, 2)}
                      </TableCell>
                      <TableCell
                        className={cn(
                          'text-right font-mono',
                          won ? 'text-green-400' : 'text-red-400',
                        )}
                      >
                        {fmtPct(t.pnl_pct)}
                      </TableCell>
                      <TableCell
                        className={cn(
                          'text-right font-mono',
                          won ? 'text-green-400' : 'text-red-400',
                        )}
                      >
                        {t.realized_r_multiple ? `${fmt(t.realized_r_multiple, 2)}R` : '—'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={exitReasonVariant(t.exit_reason)}>
                          {t.exit_reason ?? '—'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Link href={`/reviews?trade_id=${t.id}`}>
                          <Button variant="ghost" size="sm">
                            <FileText className="h-3.5 w-3.5 mr-1" /> 复盘
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function exitReasonVariant(
  reason: string | null,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' {
  if (!reason) return 'muted';
  if (reason.startsWith('TAKE_PROFIT')) return 'success';
  if (reason === 'TRAILING_STOP') return 'info';
  if (reason === 'STOP_LOSS' || reason === 'AI_RISK_EXIT') return 'danger';
  if (reason === 'MAX_HOLDING') return 'warning';
  return 'muted';
}
