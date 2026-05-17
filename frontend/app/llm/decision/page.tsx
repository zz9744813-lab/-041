'use client';

import { ArrowLeft, Brain, Play } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useSse } from '@/lib/use-sse';

const SSE_TYPES = [
  'stage',
  'scores',
  'cache_hit',
  'attempt_start',
  'attempt_done',
  'thinking_delta',
  'text_delta',
  'result',
  'error',
  'info',
];

export default function LlmDecisionPlayground() {
  const [symbol, setSymbol] = useState('AAPL');
  const [active, setActive] = useState<string | null>(null);

  const url = active ? `/api/llm/stream/decision/${encodeURIComponent(active)}` : null;
  const { events, state, reset } = useSse(url, SSE_TYPES);

  const stages = useMemo(() => events.filter((e) => e.type === 'stage'), [events]);
  const scoresEv = useMemo(() => [...events].reverse().find((e) => e.type === 'scores'), [events]);
  const thinking = useMemo(
    () => events.filter((e) => e.type === 'thinking_delta').map((e) => e.data?.text ?? '').join(''),
    [events],
  );
  const text = useMemo(
    () => events.filter((e) => e.type === 'text_delta').map((e) => e.data?.text ?? '').join(''),
    [events],
  );
  const result = useMemo(() => [...events].reverse().find((e) => e.type === 'result'), [events]);
  const errorEv = useMemo(() => [...events].reverse().find((e) => e.type === 'error'), [events]);
  const info = useMemo(() => [...events].reverse().find((e) => e.type === 'info'), [events]);

  const start = () => {
    reset();
    setActive(null);
    // tick so reset's state flush settles before resubscribing
    setTimeout(() => setActive(symbol.trim().toUpperCase()), 0);
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/llm" className="text-zinc-400 hover:text-zinc-200 flex items-center gap-1 text-sm">
          <ArrowLeft className="h-4 w-4" /> 返回列表
        </Link>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Brain className="h-6 w-6" /> 实时决策调试
        </h1>
        <p className="text-xs text-zinc-500">对单一标的运行评分 + LLM 决策，实时显示 thinking + 最终输出。不会创建持仓。</p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">输入</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="标的，如 AAPL / BTCUSD"
            className="flex-1 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded text-sm font-mono"
          />
          <Button size="sm" onClick={start} disabled={!symbol.trim() || state === 'open'}>
            <Play className="h-3.5 w-3.5 mr-1" />
            {state === 'open' ? '运行中...' : '开始'}
          </Button>
        </CardContent>
      </Card>

      {stages.length > 0 && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">阶段</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {stages.map((s, i) => (
                <Badge key={i} variant="muted" className="font-mono text-xs">{s.data?.stage ?? '—'}</Badge>
              ))}
              {state === 'open' && <Badge variant="warning">连接中...</Badge>}
              {state === 'closed' && <Badge variant="success">已结束</Badge>}
            </div>
          </CardContent>
        </Card>
      )}

      {scoresEv && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">策略评分</CardTitle>
            <CardDescription>市场环境：<span className="font-mono">{scoresEv.data?.regime ?? '—'}</span></CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {(scoresEv.data?.scores ?? []).map((s: any, i: number) => (
                <div key={i} className="bg-zinc-950 p-2 rounded text-xs">
                  <div className="flex justify-between font-mono">
                    <span>{s.model}</span>
                    <span>{s.final_score} (×{scoresEv.data?.weights_applied?.[s.model] ?? '?'})</span>
                  </div>
                  <div className="text-zinc-500 mt-1">{s.raw_reason || '—'}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {info && (
        <Card>
          <CardContent className="text-xs text-yellow-300 p-4">{info.data?.info}</CardContent>
        </Card>
      )}

      {(thinking || state === 'open') && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2"><Brain className="h-4 w-4" />思考过程</CardTitle>
            <CardDescription>模型在产出最终答案前的内部推理（仅 Claude extended thinking 启用时有内容）</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-96 overflow-auto">{thinking || '— 等待模型输出 —'}</pre>
          </CardContent>
        </Card>
      )}

      {(text || state === 'open') && (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">原始响应（流式）</CardTitle></CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-96 overflow-auto">{text || '— 等待 —'}</pre>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              结果
              <Badge variant={result.data?.ok ? 'success' : 'danger'}>{result.data?.ok ? '成功' : '失败'}</Badge>
              {result.data?.source && <Badge variant="muted">{result.data.source}</Badge>}
              {result.data?.llm_call_log_id != null && (
                <Link href={`/llm/${result.data.llm_call_log_id}`} className="text-blue-400 hover:underline text-xs">查看完整调用记录 →</Link>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-[500px] overflow-auto">{JSON.stringify(result.data?.plan ?? {}, null, 2)}</pre>
          </CardContent>
        </Card>
      )}

      {errorEv && (
        <Card>
          <CardContent className="text-xs text-red-300 p-4">错误：{errorEv.data?.error}</CardContent>
        </Card>
      )}
    </div>
  );
}
