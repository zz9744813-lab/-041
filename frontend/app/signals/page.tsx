'use client';

import { Download, Play, X } from 'lucide-react';
import { useState } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogClose, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { SignalRow } from '@/lib/types';
import { downloadCSV, fmt } from '@/lib/utils';

const STATUSES = ['', 'NEW', 'APPROVED', 'APPROVED_WAITING_ENTRY', 'EXECUTED', 'REJECTED', 'EXPIRED', 'SUPERSEDED'];

const STATUS_LABEL: Record<string, string> = {
  NEW: '新建', APPROVED: '已批准', APPROVED_WAITING_ENTRY: '等待入场',
  EXECUTED: '已执行', REJECTED: '已拒绝', EXPIRED: '已过期', SUPERSEDED: '已被替代',
};

const TYPE_LABEL: Record<string, string> = {
  TREND_BREAKOUT: '突破买入', PULLBACK_BUY: '回调买入',
  TREND_FOLLOW: '趋势跟踪', RISK_WARNING: '风险警告',
  NO_TRADE: '不开仓', INSUFFICIENT_DATA: '数据不足',
};

function statusVariant(status: string): 'success' | 'warning' | 'danger' | 'info' | 'muted' {
  if (status === 'EXECUTED') return 'success';
  if (status === 'APPROVED' || status === 'APPROVED_WAITING_ENTRY') return 'info';
  if (status === 'REJECTED') return 'danger';
  if (status === 'EXPIRED' || status === 'SUPERSEDED') return 'muted';
  return 'warning';
}

export default function Signals() {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selected, setSelected] = useState<SignalRow | null>(null);
  const [busy, setBusy] = useState(false);

  const url = `/api/signals?limit=200${statusFilter ? `&status=${statusFilter}` : ''}`;
  const { data: signals, error, mutate } = useSWR<SignalRow[]>(url, fetcher, { refreshInterval: 30000 });

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold">交易信号</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="ml-auto px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm">
          <option value="">全部状态</option>
          {STATUSES.map((s) => s && <option key={s} value={s}>{STATUS_LABEL[s] || s}</option>)}
        </select>
        <Button variant="outline" size="sm" onClick={() => signals && downloadCSV(`signals-${new Date().toISOString().slice(0, 10)}.csv`, signals.map((s) => ({ 标的: s.symbol, 类型: s.signal_type, 方向: s.direction, 置信度: s.confidence_score, 'R/R': s.risk_reward_ratio ?? '', 入场下沿: s.entry_low ?? '', 入场上沿: s.entry_high ?? '', 止损: s.stop_loss ?? '', 目标1: s.target_1 ?? '', 目标2: s.target_2 ?? '', 状态: s.status, 策略: s.model_name })))}>
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
        <Button size="sm" onClick={async () => { setBusy(true); try { await fetch('/api/signals/run', { method: 'POST' }); mutate(); } finally { setBusy(false); } }} disabled={busy}>
          <Play className="h-3.5 w-3.5 mr-1" />{busy ? '运行中...' : '触发生成'}
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>全部信号</CardTitle>
          <CardDescription>点击行查看详情</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? <ErrorState error={error} />
            : !signals ? <LoadingState />
            : signals.length === 0
            ? <EmptyState message="暂无信号" hint={<>点击「触发生成」运行策略评分或启动 <code>python -m app.scheduler</code></>} />
            : <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>标的</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>方向</TableHead>
                    <TableHead className="text-right">置信度</TableHead>
                    <TableHead className="text-right">R/R</TableHead>
                    <TableHead className="text-right">入场区间</TableHead>
                    <TableHead className="text-right">止损</TableHead>
                    <TableHead className="text-right">目标</TableHead>
                    <TableHead>状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {signals.map((s) => (
                    <TableRow key={s.id} onClick={() => setSelected(s)} className="cursor-pointer">
                      <TableCell className="font-mono">{s.symbol}</TableCell>
                      <TableCell className="text-zinc-400">{TYPE_LABEL[s.signal_type] || s.signal_type}</TableCell>
                      <TableCell className="text-zinc-400">{s.direction === 'LONG' ? '做多' : s.direction}</TableCell>
                      <TableCell className="text-right font-mono">{s.confidence_score}</TableCell>
                      <TableCell className="text-right font-mono">{s.risk_reward_ratio ?? '—'}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{s.entry_low ? `${fmt(s.entry_low)}~${fmt(s.entry_high)}` : '—'}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{s.stop_loss ? fmt(s.stop_loss) : '—'}</TableCell>
                      <TableCell className="text-right font-mono text-xs">{s.target_1 ? fmt(s.target_1) : '—'}</TableCell>
                      <TableCell><Badge variant={statusVariant(s.status)}>{STATUS_LABEL[s.status] || s.status}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
          }
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent>
          {selected && (
            <>
              <DialogHeader>
                <div>
                  <DialogTitle>{selected.symbol} · {TYPE_LABEL[selected.signal_type] || selected.signal_type}</DialogTitle>
                  <p className="text-xs text-zinc-500 mt-1">{new Date(selected.created_at).toLocaleString()} · 策略模型：{selected.model_name}</p>
                </div>
                <DialogClose />
              </DialogHeader>
              <div className="p-4 space-y-3 text-sm">
                <KV label="状态" value={<Badge variant={statusVariant(selected.status)}>{STATUS_LABEL[selected.status] || selected.status}</Badge>} />
                <KV label="方向 / 置信度" value={`${selected.direction === 'LONG' ? '做多' : selected.direction} · ${selected.confidence_score}`} />
                <KV label="入场 / 止损 / 目标" value={<span className="font-mono">{selected.entry_low ? `${fmt(selected.entry_low)} ~ ${fmt(selected.entry_high)}` : '—'} / {selected.stop_loss ? fmt(selected.stop_loss) : '—'} / {selected.target_1 ? fmt(selected.target_1) : '—'}{selected.target_2 ? ` (目标2 ${fmt(selected.target_2)})` : ''}</span>} />
                <KV label="风险收益比" value={selected.risk_reward_ratio ?? '—'} />
                <KV label="仓位比例" value={selected.position_size_pct ? `${selected.position_size_pct}%` : '—'} />
                <KV label="持仓天数" value={`${selected.expected_holding_days_min ?? '—'} ~ ${selected.expected_holding_days_max ?? '—'}`} />
                <KV label="有效期至" value={new Date(selected.valid_until).toLocaleString()} />
                <KV label="LLM 来源" value={selected.llm_provider ? `${selected.llm_provider} ${selected.llm_model ?? ''} · $${selected.llm_cost_usd ?? '0'}` : '规则引擎'} />
                <Section title="理由">
                  <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded">{selected.reason || '—'}</pre>
                </Section>
                <Section title="风险提示">
                  <p className="text-xs text-zinc-300">{selected.risk_note || '—'}</p>
                </Section>
                <Section title="失效条件">
                  <p className="text-xs text-yellow-400">{selected.invalid_condition || '—'}</p>
                </Section>
                {selected.follow_up_rule && <Section title="后续规则"><p className="text-xs text-zinc-300">{selected.follow_up_rule}</p></Section>}
                {selected.reject_reason && <Section title="拒绝原因"><p className="text-xs text-red-400">{selected.reject_reason}</p></Section>}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="flex justify-between gap-4"><span className="text-zinc-500">{label}</span><span className="text-right">{value}</span></div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><div className="text-xs font-semibold text-zinc-400 mb-1">{title}</div>{children}</div>;
}
