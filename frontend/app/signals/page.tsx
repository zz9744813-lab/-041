'use client';

import { Download, Play } from 'lucide-react';
import { useState } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogClose, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
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
import type { SignalRow } from '@/lib/types';
import { downloadCSV, fmt } from '@/lib/utils';

const STATUSES = [
  '',
  'NEW',
  'APPROVED',
  'APPROVED_WAITING_ENTRY',
  'EXECUTED',
  'REJECTED',
  'EXPIRED',
  'SUPERSEDED',
] as const;

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

  async function runNow() {
    setBusy(true);
    try {
      await fetch('/api/signals/run', { method: 'POST' });
      mutate();
    } finally {
      setBusy(false);
    }
  }

  function exportCsv() {
    if (!signals) return;
    downloadCSV(
      `signals-${new Date().toISOString().slice(0, 10)}.csv`,
      signals.map((s) => ({
        id: s.id,
        symbol: s.symbol,
        signal_type: s.signal_type,
        direction: s.direction,
        confidence: s.confidence_score,
        rr: s.risk_reward_ratio ?? '',
        entry_low: s.entry_low ?? '',
        entry_high: s.entry_high ?? '',
        stop_loss: s.stop_loss ?? '',
        target_1: s.target_1 ?? '',
        target_2: s.target_2 ?? '',
        status: s.status,
        model: s.model_name,
        created_at: s.created_at,
        valid_until: s.valid_until,
      })),
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold">信号</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="ml-auto px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s || '全部状态'}
            </option>
          ))}
        </select>
        <Button variant="outline" size="sm" onClick={exportCsv}>
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
        <Button size="sm" onClick={runNow} disabled={busy}>
          <Play className="h-3.5 w-3.5 mr-1" />
          {busy ? '运行中...' : '触发生成'}
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>所有信号</CardTitle>
          <CardDescription>点击行查看详情</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <ErrorState error={error} />
          ) : !signals ? (
            <LoadingState />
          ) : signals.length === 0 ? (
            <EmptyState
              message="暂无信号"
              hint={
                <>
                  运行 <code>python -m app.scheduler</code> 或点击右上「触发生成」按钮。
                </>
              }
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Symbol</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Conf</TableHead>
                  <TableHead className="text-right">R/R</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Stop</TableHead>
                  <TableHead className="text-right">Target</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {signals.map((s) => (
                  <TableRow
                    key={s.id}
                    onClick={() => setSelected(s)}
                    className="cursor-pointer"
                  >
                    <TableCell className="font-mono">{s.symbol}</TableCell>
                    <TableCell className="text-zinc-400">{s.signal_type}</TableCell>
                    <TableCell className="text-zinc-400">{s.direction}</TableCell>
                    <TableCell className="text-right font-mono">{s.confidence_score}</TableCell>
                    <TableCell className="text-right font-mono">
                      {s.risk_reward_ratio ?? '—'}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {s.entry_low ? `${fmt(s.entry_low)}-${fmt(s.entry_high)}` : '—'}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {s.stop_loss ? fmt(s.stop_loss) : '—'}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {s.target_1 ? fmt(s.target_1) : '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(s.status)}>{s.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent>
          {selected && (
            <>
              <DialogHeader>
                <div>
                  <DialogTitle>
                    {selected.symbol} · {selected.signal_type}
                  </DialogTitle>
                  <p className="text-xs text-zinc-500 mt-1">
                    {new Date(selected.created_at).toLocaleString()} · model={selected.model_name}
                  </p>
                </div>
                <DialogClose />
              </DialogHeader>
              <div className="p-4 space-y-3 text-sm">
                <KV label="Status" value={<Badge variant={statusVariant(selected.status)}>{selected.status}</Badge>} />
                <KV label="Direction / Confidence" value={`${selected.direction} · ${selected.confidence_score}`} />
                <KV
                  label="Entry / Stop / Target"
                  value={
                    <span className="font-mono">
                      {selected.entry_low ? `${fmt(selected.entry_low)} - ${fmt(selected.entry_high)}` : '—'}
                      {' / '}
                      {selected.stop_loss ? fmt(selected.stop_loss) : '—'}
                      {' / '}
                      {selected.target_1 ? fmt(selected.target_1) : '—'}
                      {selected.target_2 ? ` (T2 ${fmt(selected.target_2)})` : ''}
                    </span>
                  }
                />
                <KV label="R/R" value={selected.risk_reward_ratio ?? '—'} />
                <KV label="Position size %" value={selected.position_size_pct ?? '—'} />
                <KV label="Hold days" value={`${selected.expected_holding_days_min ?? '—'} ~ ${selected.expected_holding_days_max ?? '—'}`} />
                <KV label="Decay (h)" value={selected.signal_decay_hours ?? '—'} />
                <KV label="Valid until" value={new Date(selected.valid_until).toLocaleString()} />
                <KV
                  label="LLM"
                  value={
                    selected.llm_provider
                      ? `${selected.llm_provider} ${selected.llm_model ?? ''} · $${selected.llm_cost_usd ?? '0'}`
                      : 'rule-based'
                  }
                />
                <Section title="Reason">
                  <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded">
                    {selected.reason || '—'}
                  </pre>
                </Section>
                <Section title="Risk note">
                  <p className="text-xs text-zinc-300">{selected.risk_note || '—'}</p>
                </Section>
                <Section title="Invalid condition">
                  <p className="text-xs text-yellow-400">{selected.invalid_condition || '—'}</p>
                </Section>
                {selected.follow_up_rule && (
                  <Section title="Follow-up rule">
                    <p className="text-xs text-zinc-300">{selected.follow_up_rule}</p>
                  </Section>
                )}
                {selected.reject_reason && (
                  <Section title="Reject reason">
                    <p className="text-xs text-red-400">{selected.reject_reason}</p>
                  </Section>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-zinc-500">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold text-zinc-400 mb-1">{title}</div>
      {children}
    </div>
  );
}
