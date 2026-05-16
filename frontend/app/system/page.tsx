'use client';

import { Download } from 'lucide-react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { DataFreshnessRow, LlmStatRow, RejectReasonRow, SystemHealthRow } from '@/lib/types';
import { cn, downloadCSV, fmt } from '@/lib/utils';

const STATUS_LABEL: Record<string, string> = { RUNNING: '运行中', SUCCESS: '成功', FAILED: '失败' };

export default function System() {
  const { data: health } = useSWR<SystemHealthRow[]>('/api/system/health', fetcher, { refreshInterval: 30000 });
  const { data: freshness } = useSWR<DataFreshnessRow[]>('/api/system/data-freshness', fetcher, { refreshInterval: 60000 });
  const { data: llm } = useSWR<LlmStatRow[]>('/api/system/llm-stats', fetcher, { refreshInterval: 60000 });
  const { data: rejects } = useSWR<RejectReasonRow[]>('/api/system/reject-reasons', fetcher);

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">系统健康度</h1>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>任务运行记录</CardTitle>
              <CardDescription>调度器每个 job 的运行状态</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => health && downloadCSV(`system-health-${new Date().toISOString().slice(0, 10)}.csv`, health.map((h) => ({ 任务: h.job_name, 状态: h.status, 开始: h.started_at, 结束: h.finished_at ?? '', 错误: h.error_message ?? '' })))}>
              <Download className="h-3.5 w-3.5 mr-1" /> 导出
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {!health ? <LoadingState /> : health.length === 0 ? <EmptyState message="暂无任务记录" /> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务</TableHead><TableHead>开始时间</TableHead><TableHead>状态</TableHead><TableHead>耗时</TableHead><TableHead>错误信息</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {health.slice(0, 30).map((h) => {
                  const dur = h.started_at && h.finished_at ? `${((new Date(h.finished_at).getTime() - new Date(h.started_at).getTime()) / 1000).toFixed(1)}s` : '—';
                  return (
                    <TableRow key={h.id}>
                      <TableCell className="font-mono">{h.job_name}</TableCell>
                      <TableCell className="text-zinc-500 text-xs">{new Date(h.started_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant={h.status === 'SUCCESS' ? 'success' : h.status === 'FAILED' ? 'danger' : 'warning'}>
                          {STATUS_LABEL[h.status] || h.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-zinc-400">{dur}</TableCell>
                      <TableCell className="text-red-400 text-xs max-w-md truncate">{h.error_message ?? ''}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>数据新鲜度</CardTitle>
          <CardDescription>每个标的的最新 K 线时间</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {!freshness ? <LoadingState /> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>标的</TableHead><TableHead>周期</TableHead><TableHead>最新 bar</TableHead><TableHead className="text-right">延迟(分)</TableHead><TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {freshness.map((f, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-mono">{f.symbol}</TableCell>
                    <TableCell className="text-zinc-400">{f.timeframe}</TableCell>
                    <TableCell className="text-zinc-500 text-xs">{f.actual ?? '—'}</TableCell>
                    <TableCell className="text-right">{f.skew_minutes !== null ? f.skew_minutes.toFixed(0) : '—'}</TableCell>
                    <TableCell><Badge variant={f.status === 'STALE' ? 'danger' : 'success'}>{f.status === 'STALE' ? '延迟' : '正常'}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>LLM 调用统计（近 7 天）</CardTitle>
            <CardDescription>费用 / 缓存命中 / 失败率</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {!llm ? <LoadingState /> : llm.length === 0 ? <EmptyState message="暂无 LLM 调用" height={60} /> : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>日期</TableHead><TableHead>用途</TableHead><TableHead className="text-right">调用</TableHead><TableHead className="text-right">缓存</TableHead><TableHead className="text-right">费用</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {llm.map((l: LlmStatRow, i: number) => (
                    <TableRow key={i}>
                      <TableCell className="text-zinc-400 text-xs">{l.day}</TableCell>
                      <TableCell className="text-zinc-400">{l.purpose === 'signal_generation' ? '信号生成' : l.purpose === 'review' ? '复盘' : l.purpose}</TableCell>
                      <TableCell className="text-right font-mono">{l.total}</TableCell>
                      <TableCell className="text-right font-mono">{l.cached_hits}</TableCell>
                      <TableCell className="text-right font-mono">${fmt(l.cost_usd, 4)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>风控拒绝原因（近 7 天）</CardTitle>
            <CardDescription>高拒绝率说明风控可能过于严厉</CardDescription>
          </CardHeader>
          <CardContent>
            {!rejects ? <LoadingState /> : rejects.length === 0 ? <p className="text-zinc-500 text-xs">暂无拒绝记录</p> : (
              <ul className="text-sm space-y-1.5">
                {rejects.map((r, i) => (
                  <li key={i} className="flex justify-between items-center">
                    <span className={cn('text-zinc-400 text-xs truncate flex-1', r.n > 5 && 'text-yellow-400')}>{r.reason}</span>
                    <Badge variant={r.n > 10 ? 'danger' : r.n > 5 ? 'warning' : 'muted'}>{r.n}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
