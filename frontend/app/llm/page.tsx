'use client';

import { Brain, Eye } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { LlmCallLogListItem } from '@/lib/types';

const PAGE_SIZE = 50;

const PURPOSES = ['', 'signal_generation', 'review'];
const PURPOSE_LABEL: Record<string, string> = {
  signal_generation: '信号生成',
  review: '交易复盘',
};

const STATUS_LABEL: Record<string, string> = {
  SUCCESS: '成功',
  API_ERROR: '调用失败',
};

function statusVariant(status: string): 'success' | 'danger' | 'warning' | 'muted' {
  if (status === 'SUCCESS') return 'success';
  if (status === 'API_ERROR') return 'danger';
  return 'warning';
}

export default function LlmLogs() {
  const [page, setPage] = useState(0);
  const [purpose, setPurpose] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [days, setDays] = useState<number>(7);

  const params = new URLSearchParams({
    days: String(days),
    limit: String(PAGE_SIZE),
    offset: String(page * PAGE_SIZE),
  });
  if (purpose) params.set('purpose', purpose);
  if (status) params.set('status', status);

  const { data: logs, error } = useSWR<LlmCallLogListItem[]>(
    `/api/system/llm-logs?${params.toString()}`,
    fetcher,
    { refreshInterval: 60000 },
  );

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Brain className="h-6 w-6" /> LLM 调用日志
        </h1>
        <p className="text-xs text-zinc-500 ml-2">每次发给 LLM 的 prompt / 输入 / 思考 / 原始响应都在此</p>
        <div className="ml-auto flex gap-2 items-center">
          <select value={purpose} onChange={(e) => { setPage(0); setPurpose(e.target.value); }} className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm">
            <option value="">全部用途</option>
            {PURPOSES.map((p) => p && <option key={p} value={p}>{PURPOSE_LABEL[p] || p}</option>)}
          </select>
          <select value={status} onChange={(e) => { setPage(0); setStatus(e.target.value); }} className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm">
            <option value="">全部状态</option>
            <option value="SUCCESS">成功</option>
            <option value="API_ERROR">失败</option>
          </select>
          <select value={days} onChange={(e) => { setPage(0); setDays(Number(e.target.value)); }} className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm">
            <option value={1}>近 1 天</option>
            <option value={7}>近 7 天</option>
            <option value={30}>近 30 天</option>
            <option value={90}>近 90 天</option>
          </select>
          <Link href="/llm/cost-attribution" className="text-xs text-blue-400 hover:underline">成本归因 →</Link>
          <Link href="/llm/decision" className="text-xs text-blue-400 hover:underline">实时调试 →</Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>调用记录</CardTitle>
          <CardDescription>点击「详情」查看 prompt / 输入 / 思考 / 原始响应</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? <ErrorState error={error} />
            : !logs ? <LoadingState />
            : logs.length === 0
            ? <EmptyState message="暂无 LLM 调用记录" hint="设置 ENABLE_LLM_DECISION=true 后会出现" />
            : <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>时间</TableHead>
                    <TableHead>用途</TableHead>
                    <TableHead>提供商 / 模型</TableHead>
                    <TableHead>缓存</TableHead>
                    <TableHead className="text-right">尝试</TableHead>
                    <TableHead className="text-right">输入 token</TableHead>
                    <TableHead className="text-right">输出 token</TableHead>
                    <TableHead className="text-right">成本</TableHead>
                    <TableHead className="text-right">延迟</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell className="text-zinc-500 text-xs whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</TableCell>
                      <TableCell><Badge variant="muted">{PURPOSE_LABEL[r.purpose] || r.purpose}</Badge></TableCell>
                      <TableCell className="text-xs"><span className="text-zinc-400">{r.provider}</span> · <span className="font-mono">{r.model}</span></TableCell>
                      <TableCell>{r.cached ? <Badge variant="success">命中</Badge> : '—'}</TableCell>
                      <TableCell className="text-right font-mono">{r.attempts ?? '—'}</TableCell>
                      <TableCell className="text-right font-mono">{r.input_tokens ?? '—'}</TableCell>
                      <TableCell className="text-right font-mono">{r.output_tokens ?? '—'}</TableCell>
                      <TableCell className="text-right font-mono">${r.cost_usd ?? '0'}</TableCell>
                      <TableCell className="text-right font-mono">{r.latency_ms != null ? `${r.latency_ms} ms` : '—'}</TableCell>
                      <TableCell><Badge variant={statusVariant(r.status)}>{STATUS_LABEL[r.status] || r.status}</Badge></TableCell>
                      <TableCell><Link href={`/llm/${r.id}`} className="text-blue-400 hover:underline text-xs flex items-center gap-1"><Eye className="h-3 w-3" />详情</Link></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
          }
        </CardContent>
        <div className="flex items-center justify-between p-3 border-t border-zinc-800 text-xs text-zinc-500">
          <div>第 {page + 1} 页 · 每页 {PAGE_SIZE} 条</div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>上一页</Button>
            <Button variant="outline" size="sm" disabled={!logs || logs.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>下一页</Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
