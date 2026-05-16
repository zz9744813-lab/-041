'use client';

import { Download } from 'lucide-react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type {
  DataFreshnessRow,
  LlmStatRow,
  RejectReasonRow,
  SystemHealthRow,
} from '@/lib/types';
import { cn, downloadCSV, fmt } from '@/lib/utils';

export default function System() {
  const { data: health } = useSWR<SystemHealthRow[]>('/api/system/health', fetcher, {
    refreshInterval: 30000,
  });
  const { data: freshness } = useSWR<DataFreshnessRow[]>(
    '/api/system/data-freshness',
    fetcher,
    { refreshInterval: 60000 },
  );
  const { data: llm } = useSWR<LlmStatRow[]>('/api/system/llm-stats', fetcher, {
    refreshInterval: 60000,
  });
  const { data: rejects } = useSWR<RejectReasonRow[]>('/api/system/reject-reasons', fetcher);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">系统健康度</h1>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>最近任务运行</CardTitle>
              <CardDescription>每个 job 的 SystemHealth 记录</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                downloadCSV(
                  `system-health-${new Date().toISOString().slice(0, 10)}.csv`,
                  (health ?? []).map((h) => ({
                    job: h.job_name,
                    status: h.status,
                    started: h.started_at,
                    finished: h.finished_at ?? '',
                    error: h.error_message ?? '',
                  })),
                )
              }
            >
              <Download className="h-3.5 w-3.5 mr-1" /> 导出
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {health?.slice(0, 30).map((h) => {
                const dur =
                  h.started_at && h.finished_at
                    ? `${(
                        (new Date(h.finished_at).getTime() - new Date(h.started_at).getTime()) /
                        1000
                      ).toFixed(1)}s`
                    : '—';
                return (
                  <TableRow key={h.id}>
                    <TableCell className="font-mono">{h.job_name}</TableCell>
                    <TableCell className="text-zinc-500 text-xs">
                      {new Date(h.started_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          h.status === 'SUCCESS'
                            ? 'success'
                            : h.status === 'FAILED'
                              ? 'danger'
                              : 'warning'
                        }
                      >
                        {h.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-zinc-400">{dur}</TableCell>
                    <TableCell className="text-red-400 text-xs max-w-md truncate">
                      {h.error_message ?? ''}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>数据新鲜度</CardTitle>
          <CardDescription>每个 symbol/timeframe 的最新 final bar</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Symbol</TableHead>
                <TableHead>TF</TableHead>
                <TableHead>Last bar</TableHead>
                <TableHead className="text-right">Skew (min)</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {freshness?.map((f, i) => (
                <TableRow key={i}>
                  <TableCell className="font-mono">{f.symbol}</TableCell>
                  <TableCell className="text-zinc-400">{f.timeframe}</TableCell>
                  <TableCell className="text-zinc-500 text-xs">{f.actual ?? '—'}</TableCell>
                  <TableCell className="text-right">
                    {f.skew_minutes !== null ? f.skew_minutes.toFixed(0) : '—'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={f.status === 'STALE' ? 'danger' : 'success'}>{f.status}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>LLM 调用统计 (近 7 天)</CardTitle>
            <CardDescription>cost / cache hit / failure</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Day</TableHead>
                  <TableHead>Purpose</TableHead>
                  <TableHead className="text-right">Calls</TableHead>
                  <TableHead className="text-right">Cached</TableHead>
                  <TableHead className="text-right">Cost $</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {llm?.map((l, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-zinc-400 text-xs">{l.day}</TableCell>
                    <TableCell className="text-zinc-400">{l.purpose}</TableCell>
                    <TableCell className="text-right font-mono">{l.total}</TableCell>
                    <TableCell className="text-right font-mono">{l.cached_hits}</TableCell>
                    <TableCell className="text-right font-mono">${fmt(l.cost_usd, 4)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {(!llm || llm.length === 0) && (
              <p className="text-zinc-500 p-4 text-sm">暂无 LLM 调用</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>风控拒绝 Top 原因</CardTitle>
            <CardDescription>近 7 天 reject_reason 直方图</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm space-y-1.5">
              {rejects?.map((r, i) => (
                <li key={i} className="flex justify-between items-center">
                  <span
                    className={cn(
                      'text-zinc-400 text-xs truncate flex-1',
                      r.n > 5 && 'text-yellow-400',
                    )}
                  >
                    {r.reason}
                  </span>
                  <Badge variant={r.n > 10 ? 'danger' : r.n > 5 ? 'warning' : 'muted'}>
                    {r.n}
                  </Badge>
                </li>
              ))}
              {(!rejects || rejects.length === 0) && (
                <p className="text-zinc-500 text-xs">暂无拒绝</p>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
