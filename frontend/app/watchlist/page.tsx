'use client';

import { Download } from 'lucide-react';
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
import type { Asset } from '@/lib/types';
import { downloadCSV } from '@/lib/utils';

export default function Watchlist() {
  const { data: assets, error, isLoading } = useSWR<Asset[]>(
    '/api/assets?active_only=true',
    fetcher,
  );

  const exportCsv = () => {
    if (!assets) return;
    downloadCSV(
      `watchlist-${new Date().toISOString().slice(0, 10)}.csv`,
      assets.map((a) => ({
        symbol: a.symbol,
        name: a.name,
        market: a.market,
        asset_type: a.asset_type,
        sector: a.sector ?? '',
        priority: a.priority,
      })),
    );
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">观察池</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={exportCsv}
          disabled={!assets || assets.length === 0}
          className="ml-auto"
        >
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>当前 active 资产</CardTitle>
          <CardDescription>spec § 2.2-2.3 默认观察池</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <ErrorState error={error} />
          ) : isLoading || !assets ? (
            <LoadingState />
          ) : assets.length === 0 ? (
            <EmptyState
              message="还没有 Asset"
              hint={
                <>
                  <code>POST /api/assets</code> 创建。spec § 2.2 默认观察池有 20 个美股 + BTC + ETH。
                </>
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Market</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Sector</TableHead>
                  <TableHead className="text-right">Priority</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {assets.map((a) => (
                  <TableRow key={a.id}>
                    <TableCell className="font-mono">{a.symbol}</TableCell>
                    <TableCell>{a.name}</TableCell>
                    <TableCell>
                      <Badge variant={a.market === 'CRYPTO' ? 'warning' : 'info'}>
                        {a.market}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="muted">{a.asset_type}</Badge>
                    </TableCell>
                    <TableCell className="text-zinc-400">{a.sector ?? '—'}</TableCell>
                    <TableCell className="text-right text-zinc-400">{a.priority}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
