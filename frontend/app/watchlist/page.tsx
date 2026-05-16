'use client';

import { Download } from 'lucide-react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { Asset } from '@/lib/types';
import { downloadCSV } from '@/lib/utils';

export default function Watchlist() {
  const { data: assets, error } = useSWR<Asset[]>('/api/assets?active_only=true', fetcher);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">观察池</h1>
        <Button variant="outline" size="sm" onClick={() => assets && downloadCSV(`watchlist-${new Date().toISOString().slice(0, 10)}.csv`, assets.map((a) => ({ symbol: a.symbol, 名称: a.name, 市场: a.market, 类型: a.asset_type, 板块: a.sector ?? '', 优先级: a.priority })))} disabled={!assets || assets.length === 0} className="ml-auto">
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>当前活跃资产</CardTitle>
          <CardDescription>默认观察池共 22 个标的（20 美股 + BTC + ETH）</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? <ErrorState error={error} />
            : !assets ? <LoadingState />
            : assets.length === 0
            ? <EmptyState message="还没有资产" hint={<>通过 <code>POST /api/assets</code> 添加</>} />
            : <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>代码</TableHead>
                    <TableHead>名称</TableHead>
                    <TableHead>市场</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>板块</TableHead>
                    <TableHead className="text-right">优先级</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {assets.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="font-mono">{a.symbol}</TableCell>
                      <TableCell>{a.name}</TableCell>
                      <TableCell><Badge variant={a.market === 'CRYPTO' ? 'warning' : 'info'}>{a.market === 'CRYPTO' ? '加密' : '美股'}</Badge></TableCell>
                      <TableCell><Badge variant="muted">{a.asset_type}</Badge></TableCell>
                      <TableCell className="text-zinc-400">{a.sector ?? '—'}</TableCell>
                      <TableCell className="text-right text-zinc-400">{a.priority}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
          }
        </CardContent>
      </Card>
    </div>
  );
}
