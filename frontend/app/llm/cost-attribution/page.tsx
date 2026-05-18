'use client';

import { ArrowLeft, DollarSign } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { LlmBudgetInfo, LlmCostAttributionRow } from '@/lib/types';

type GroupKey = 'symbol' | 'model' | 'purpose';

export default function CostAttribution() {
  const [group, setGroup] = useState<GroupKey>('symbol');
  const [days, setDays] = useState(7);

  const { data: rows, error } = useSWR<LlmCostAttributionRow[]>(
    `/api/system/llm-cost-attribution?days=${days}&group=${group}`,
    fetcher,
    { refreshInterval: 60000 },
  );
  const { data: budget } = useSWR<LlmBudgetInfo>('/api/system/llm-budget', fetcher, {
    refreshInterval: 30000,
  });

  const total = (rows ?? []).reduce((acc, r) => acc + Number(r.cost_usd || 0), 0);
  const max = (rows ?? []).reduce(
    (acc, r) => Math.max(acc, Number(r.cost_usd || 0)),
    0,
  );

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/llm" className="text-zinc-400 hover:text-zinc-200 flex items-center gap-1 text-sm">
          <ArrowLeft className="h-4 w-4" /> 返回列表
        </Link>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <DollarSign className="h-6 w-6" />LLM 成本归因
        </h1>
        <p className="text-xs text-zinc-500">按标的 / 模型 / 用途分组统计 LLM 调用花销（不含缓存命中）。</p>
      </div>

      {budget && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">今日预算</CardTitle>
            <CardDescription>
              {budget.enforced
                ? '配置了 max_daily_llm_cost_usd，超额的调用会自动短路并记为 BUDGET_EXCEEDED。'
                : '未配置上限。在 .env 设置 MAX_DAILY_LLM_COST_USD 来开启硬上限。'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-3">
              <div className="text-2xl font-mono">${budget.spent_usd}</div>
              <div className="text-sm text-zinc-500">/ 上限 ${budget.cap_usd}</div>
              {budget.remaining_usd && <Badge variant="muted">剩余 ${budget.remaining_usd}</Badge>}
            </div>
            {budget.enforced && Number(budget.cap_usd) > 0 && (
              <div className="mt-2 h-2 bg-zinc-900 rounded overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all"
                  style={{
                    width: `${Math.min(100, (Number(budget.spent_usd) / Number(budget.cap_usd)) * 100)}%`,
                  }}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle className="text-base">分组聚合</CardTitle>
            <div className="ml-auto flex gap-2 items-center">
              <select value={group} onChange={(e) => setGroup(e.target.value as GroupKey)} className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm">
                <option value="symbol">按标的</option>
                <option value="model">按模型</option>
                <option value="purpose">按用途</option>
              </select>
              <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm">
                <option value={1}>近 1 天</option>
                <option value={7}>近 7 天</option>
                <option value={30}>近 30 天</option>
                <option value={90}>近 90 天</option>
              </select>
            </div>
          </div>
          <CardDescription>共计 ${total.toFixed(4)}</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? <ErrorState error={error} />
            : !rows ? <LoadingState />
            : rows.length === 0
            ? <EmptyState message="无 LLM 调用花销" hint="只统计非缓存的成功调用" />
            : <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{group === 'symbol' ? '标的' : group === 'model' ? '模型' : '用途'}</TableHead>
                    <TableHead className="text-right">调用次数</TableHead>
                    <TableHead className="text-right">输入 tokens</TableHead>
                    <TableHead className="text-right">输出 tokens</TableHead>
                    <TableHead className="text-right">成本 USD</TableHead>
                    <TableHead>占比</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((r) => (
                    <TableRow key={r.key}>
                      <TableCell className="font-mono text-xs">{r.key}</TableCell>
                      <TableCell className="text-right font-mono">{r.calls}</TableCell>
                      <TableCell className="text-right font-mono">{r.input_tokens.toLocaleString()}</TableCell>
                      <TableCell className="text-right font-mono">{r.output_tokens.toLocaleString()}</TableCell>
                      <TableCell className="text-right font-mono">${r.cost_usd}</TableCell>
                      <TableCell>
                        <div className="h-1.5 bg-zinc-900 rounded overflow-hidden w-32">
                          <div
                            className="h-full bg-blue-600"
                            style={{ width: `${max > 0 ? (Number(r.cost_usd) / max) * 100 : 0}%` }}
                          />
                        </div>
                      </TableCell>
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
