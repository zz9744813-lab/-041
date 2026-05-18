'use client';

import { Activity, Brain, Download, ExternalLink, Play } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useReducer, useRef, useState } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogClose, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { fetcher } from '@/lib/fetcher';
import type { SignalDetail, SignalRow, TradeRow } from '@/lib/types';
import { useSse, type SseEvent } from '@/lib/use-sse';
import { downloadCSV, fmt } from '@/lib/utils';

const STATUSES = ['', 'NEW', 'APPROVED', 'APPROVED_WAITING_ENTRY', 'EXECUTED', 'REJECTED', 'EXPIRED', 'SUPERSEDED'];
const PAGE_SIZE = 50;

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
  const [page, setPage] = useState<number>(0);
  const [selected, setSelected] = useState<SignalRow | null>(null);
  const [runJobId, setRunJobId] = useState<string | null>(null);

  const url = `/api/signals?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}${statusFilter ? `&status=${statusFilter}` : ''}`;
  const { data: signals, error, mutate } = useSWR<SignalRow[]>(url, fetcher, { refreshInterval: 60000 });

  const startRun = async () => {
    setRunJobId(null);
    const r = await fetch('/api/signals/run', { method: 'POST' });
    if (r.ok) {
      const body = (await r.json()) as { job_id: string };
      setRunJobId(body.job_id);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold">交易信号</h1>
        <select
          value={statusFilter}
          onChange={(e) => { setPage(0); setStatusFilter(e.target.value); }}
          className="ml-auto px-2 py-1 bg-zinc-900 border border-zinc-800 rounded text-sm"
        >
          <option value="">全部状态</option>
          {STATUSES.map((s) => s && <option key={s} value={s}>{STATUS_LABEL[s] || s}</option>)}
        </select>
        <Button
          variant="outline"
          size="sm"
          disabled={!signals || signals.length === 0}
          onClick={() => signals && downloadCSV(`signals-${new Date().toISOString().slice(0, 10)}.csv`, signals.map((s) => ({
            标的: s.symbol, 类型: s.signal_type, 方向: s.direction, 置信度: s.confidence_score,
            'R/R': s.risk_reward_ratio ?? '', 入场下沿: s.entry_low ?? '', 入场上沿: s.entry_high ?? '',
            止损: s.stop_loss ?? '', 目标1: s.target_1 ?? '', 目标2: s.target_2 ?? '',
            状态: s.status, 拒绝原因: s.reject_reason ?? '', 策略: s.model_name,
          })))}
        >
          <Download className="h-3.5 w-3.5 mr-1" /> 导出 CSV
        </Button>
        <Button size="sm" onClick={startRun} disabled={!!runJobId}>
          <Play className="h-3.5 w-3.5 mr-1" />{runJobId ? '运行中...' : '触发生成'}
        </Button>
      </div>

      {runJobId && (
        <RunProgress
          jobId={runJobId}
          onDone={() => {
            setRunJobId(null);
            mutate();
          }}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle>全部信号</CardTitle>
          <CardDescription>点击行查看详情；左下角分页</CardDescription>
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
                    <TableHead>备注</TableHead>
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
                      <TableCell className="text-xs text-red-400 max-w-[260px] truncate" title={s.reject_reason ?? ''}>
                        {s.status === 'REJECTED' ? s.reject_reason : ''}
                      </TableCell>
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
            <Button variant="outline" size="sm" disabled={!signals || signals.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}>下一页</Button>
          </div>
        </div>
      </Card>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent>{selected && <SignalDialog signalId={selected.id} />}</DialogContent>
      </Dialog>
    </div>
  );
}

function SignalDialog({ signalId }: { signalId: number }) {
  const { data: detail } = useSWR<SignalDetail>(`/api/signals/${signalId}`, fetcher);
  // Linked trade: only fetched once we know the signal id. SWR handles dedupe.
  const { data: linkedTrade } = useSWR<TradeRow | null>(
    detail ? `/api/signals/${signalId}/trade` : null,
    fetcher,
  );
  if (!detail) return <div className="p-6"><LoadingState /></div>;

  const ss = detail.strategy_score;
  return (
    <>
      <DialogHeader>
        <div>
          <DialogTitle>{detail.symbol} · {TYPE_LABEL[detail.signal_type] || detail.signal_type}</DialogTitle>
          <p className="text-xs text-zinc-500 mt-1">{new Date(detail.created_at).toLocaleString()} · 策略模型：{detail.model_name}</p>
        </div>
        <DialogClose />
      </DialogHeader>
      <div className="p-4 space-y-3 text-sm">
        <KV label="状态" value={<Badge variant={statusVariant(detail.status)}>{STATUS_LABEL[detail.status] || detail.status}</Badge>} />
        <KV label="方向 / 置信度" value={`${detail.direction === 'LONG' ? '做多' : detail.direction} · ${detail.confidence_score}`} />
        <KV label="入场 / 止损 / 目标" value={<span className="font-mono">{detail.entry_low ? `${fmt(detail.entry_low)} ~ ${fmt(detail.entry_high)}` : '—'} / {detail.stop_loss ? fmt(detail.stop_loss) : '—'} / {detail.target_1 ? fmt(detail.target_1) : '—'}{detail.target_2 ? ` (目标2 ${fmt(detail.target_2)})` : ''}</span>} />
        <KV label="风险收益比" value={detail.risk_reward_ratio ?? '—'} />
        <KV label="仓位比例" value={detail.position_size_pct ? `${detail.position_size_pct}%` : '—'} />
        <KV label="持仓天数" value={`${detail.expected_holding_days_min ?? '—'} ~ ${detail.expected_holding_days_max ?? '—'}`} />
        <KV label="有效期至" value={new Date(detail.valid_until).toLocaleString()} />
        <KV
          label="LLM 来源"
          value={
            detail.llm_provider ? (
              <span className="flex items-center gap-2">
                <span>{detail.llm_provider} {detail.llm_model ?? ''} · ${detail.llm_cost_usd ?? '0'}</span>
                {detail.llm_call_log_id != null && (
                  <Link href={`/llm/${detail.llm_call_log_id}`} className="text-blue-400 hover:underline text-xs flex items-center gap-1">
                    <ExternalLink className="h-3 w-3" />查看完整调用
                  </Link>
                )}
              </span>
            ) : '规则引擎'
          }
        />
        {linkedTrade && (
          <KV
            label="关联交易"
            value={
              <Link href={`/trades?trade_id=${linkedTrade.id}`} className="text-blue-400 hover:underline text-xs flex items-center gap-1 justify-end">
                <ExternalLink className="h-3 w-3" />交易 #{linkedTrade.id} · {linkedTrade.status}
                {linkedTrade.realized_r_multiple != null && <span className="text-zinc-500 ml-1">{linkedTrade.realized_r_multiple}R</span>}
              </Link>
            }
          />
        )}

        {ss && (
          <Section title="策略评分明细 (StrategyScore)">
            <div className="bg-zinc-950 p-3 rounded text-xs space-y-1">
              <div className="flex justify-between"><span className="text-zinc-500">final_score</span><span className="font-mono">{ss.final_score}</span></div>
              {ss.trend_score != null && <Sub label="trend_score" value={ss.trend_score} />}
              {ss.setup_score != null && <Sub label="setup_score" value={ss.setup_score} />}
              {ss.risk_score != null && <Sub label="risk_score" value={ss.risk_score} />}
              {ss.volume_score != null && <Sub label="volume_score" value={ss.volume_score} />}
              {ss.market_regime_score != null && <Sub label="market_regime_score" value={ss.market_regime_score} />}
              {ss.risk_reward_score != null && <Sub label="risk_reward_score" value={ss.risk_reward_score} />}
              {ss.suggested_action && <Sub label="suggested_action" value={ss.suggested_action} />}
              {ss.raw_reason && (
                <div className="pt-1 border-t border-zinc-800 mt-1">
                  <div className="text-zinc-500 mb-1">raw_reason</div>
                  <div className="text-zinc-300 whitespace-pre-wrap">{ss.raw_reason}</div>
                </div>
              )}
            </div>
          </Section>
        )}

        <Section title="理由"><pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded">{detail.reason || '—'}</pre></Section>
        <Section title="风险提示"><p className="text-xs text-zinc-300">{detail.risk_note || '—'}</p></Section>
        <Section title="失效条件"><p className="text-xs text-yellow-400">{detail.invalid_condition || '—'}</p></Section>
        {detail.follow_up_rule && <Section title="后续规则"><p className="text-xs text-zinc-300">{detail.follow_up_rule}</p></Section>}
        {detail.reject_reason && <Section title="拒绝原因"><p className="text-xs text-red-400">{detail.reject_reason}</p></Section>}
      </div>
    </>
  );
}

interface RunState {
  total: number;
  done: number;
  current: string | null;
  finished: boolean;
  // Per-asset transcript: latest asset only.
  latestSymbol: string | null;
  latestThinking: string;
  latestText: string;
}

const initialRunState: RunState = {
  total: 0,
  done: 0,
  current: null,
  finished: false,
  latestSymbol: null,
  latestThinking: '',
  latestText: '',
};

function runReducer(state: RunState, ev: SseEvent): RunState {
  // Incremental update -> O(1) per event instead of O(events).
  switch (ev.type) {
    case 'asset_total':
      return { ...state, total: Number(ev.data?.total ?? 0) };
    case 'asset_start':
      return {
        ...state,
        current: ev.data?.symbol ?? null,
        latestSymbol: ev.data?.symbol ?? state.latestSymbol,
        latestThinking: '',
        latestText: '',
      };
    case 'asset_done':
    case 'asset_error':
      return { ...state, done: state.done + 1 };
    case 'thinking_delta':
      return { ...state, latestThinking: state.latestThinking + (ev.data?.text ?? '') };
    case 'text_delta':
      return { ...state, latestText: state.latestText + (ev.data?.text ?? '') };
    case 'finished':
      return { ...state, finished: true };
    default:
      return state;
  }
}

function RunProgress({ jobId, onDone }: { jobId: string; onDone: () => void }) {
  const sseTypes = useMemo(
    () => [
      'queued', 'started', 'asset_total', 'asset_start', 'asset_done', 'asset_error',
      'attempt_start', 'attempt_done', 'thinking_delta', 'text_delta',
      'cache_hit', 'budget_exceeded', 'finished',
    ],
    [],
  );
  const { events, state } = useSse(`/api/llm/stream/run-signals/${jobId}`, sseTypes);

  // Reduce events -> small state object instead of recomputing transcript on
  // every render (was O(events) per render, quadratic in total).
  const [runState, dispatch] = useReducer(runReducer, initialRunState);
  const lastEventCountRef = useRef(0);
  // Apply all new events on each render. The reducer is pure & cheap.
  useEffect(() => {
    for (let i = lastEventCountRef.current; i < events.length; i++) {
      dispatch(events[i]);
    }
    lastEventCountRef.current = events.length;
  }, [events]);

  const finished = runState.finished || state === 'closed';

  // onDone in an effect so we don't fire it on every render (was a render-body
  // setTimeout that scheduled onDone repeatedly).
  useEffect(() => {
    if (finished && runState.total > 0 && runState.done >= runState.total) {
      const t = setTimeout(onDone, 200);
      return () => clearTimeout(t);
    }
  }, [finished, runState.total, runState.done, onDone]);

  const transcript = runState.latestThinking || runState.latestText;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Activity className="h-4 w-4" />
          运行进度 {runState.total > 0 && <span className="text-zinc-500 text-sm font-normal">{runState.done}/{runState.total}</span>}
          {finished && <Badge variant="success">完成</Badge>}
        </CardTitle>
        <CardDescription>正在分析 {runState.current ? <span className="font-mono">{runState.current}</span> : '—'}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {runState.total > 0 && (
          <div className="h-2 bg-zinc-900 rounded overflow-hidden">
            <div className="h-full bg-blue-600 transition-all" style={{ width: `${(runState.done / runState.total) * 100}%` }} />
          </div>
        )}
        {transcript && (
          <div>
            <div className="text-xs font-semibold text-zinc-400 mb-1 flex items-center gap-1">
              <Brain className="h-3 w-3" /> LLM 流式输出 {runState.latestSymbol && <span className="text-zinc-500">— {runState.latestSymbol}</span>}
            </div>
            <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-64 overflow-auto">
              {runState.latestThinking}
              {runState.latestThinking && runState.latestText && '\n\n--- 答复 ---\n'}
              {runState.latestText}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return <div className="flex justify-between gap-4"><span className="text-zinc-500">{label}</span><span className="text-right">{value}</span></div>;
}

function Sub({ label, value }: { label: string; value: number | string }) {
  return <div className="flex justify-between"><span className="text-zinc-500">{label}</span><span className="font-mono">{value}</span></div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><div className="text-xs font-semibold text-zinc-400 mb-1">{title}</div>{children}</div>;
}
