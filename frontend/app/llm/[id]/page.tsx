'use client';

import { ArrowLeft, Brain, Code2, FileJson, MessageSquare } from 'lucide-react';
import Link from 'next/link';
import { use } from 'react';
import useSWR from 'swr';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ErrorState, LoadingState } from '@/components/ui/states';
import { fetcher } from '@/lib/fetcher';
import type { LlmCallLogDetail } from '@/lib/types';

const PURPOSE_LABEL: Record<string, string> = {
  signal_generation: '信号生成',
  review: '交易复盘',
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function LlmLogDetail({ params }: PageProps) {
  const { id } = use(params);
  const { data: log, error } = useSWR<LlmCallLogDetail>(`/api/system/llm-logs/${id}`, fetcher);

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Link href="/llm" className="text-zinc-400 hover:text-zinc-200 flex items-center gap-1 text-sm">
          <ArrowLeft className="h-4 w-4" /> 返回列表
        </Link>
      </div>

      {error ? <ErrorState error={error} />
        : !log ? <LoadingState />
        : (
          <>
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="h-5 w-5" />
                      LLM 调用 #{log.id}
                      <Badge variant={log.status === 'SUCCESS' ? 'success' : 'danger'}>{log.status}</Badge>
                      {log.cached && <Badge variant="muted">缓存命中</Badge>}
                    </CardTitle>
                    <CardDescription>
                      {new Date(log.created_at).toLocaleString()} · {PURPOSE_LABEL[log.purpose] || log.purpose} · {log.provider} {log.model} · 提示版本 {log.prompt_version}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <Stat label="尝试次数" value={String(log.attempts ?? '—')} />
                  <Stat label="输入 tokens" value={log.input_tokens?.toLocaleString() ?? '—'} />
                  <Stat label="输出 tokens" value={log.output_tokens?.toLocaleString() ?? '—'} />
                  <Stat label="成本 USD" value={`$${log.cost_usd ?? '0'}`} />
                  <Stat label="延迟" value={log.latency_ms != null ? `${log.latency_ms} ms` : '—'} />
                  <Stat label="标的" value={log.symbol ?? '—'} mono />
                  <Stat label="input_hash" value={log.input_hash.slice(0, 12) + '…'} mono />
                </div>
                {log.error_message && (
                  <div className="mt-3 p-3 bg-red-950/30 border border-red-800 rounded text-xs text-red-300 whitespace-pre-wrap">
                    {log.error_message}
                  </div>
                )}
              </CardContent>
            </Card>

            {log.attempt_history && log.attempt_history.length > 0 && (
              <Block icon={<Brain className="h-4 w-4" />} title="尝试历史 (Attempt History)" hint="每次尝试的完整记录。失败的重试也会保留原始文本和错误。">
                <div className="space-y-3">
                  {log.attempt_history.map((a) => (
                    <div key={a.n} className="bg-zinc-950 p-3 rounded text-xs space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={a.ok ? 'success' : 'danger'}>第 {a.n} 次 · {a.ok ? '成功' : '失败'}</Badge>
                        {a.input_tokens != null && <span className="text-zinc-500">in {a.input_tokens}</span>}
                        {a.output_tokens != null && <span className="text-zinc-500">out {a.output_tokens}</span>}
                        {a.latency_ms != null && <span className="text-zinc-500">{a.latency_ms} ms</span>}
                      </div>
                      {a.error && <div className="text-red-400 whitespace-pre-wrap">{a.error}</div>}
                      {a.thinking && (
                        <details>
                          <summary className="cursor-pointer text-zinc-400">思考</summary>
                          <pre className="whitespace-pre-wrap text-zinc-300 mt-2 max-h-64 overflow-auto">{a.thinking}</pre>
                        </details>
                      )}
                      {a.raw_text && (
                        <details>
                          <summary className="cursor-pointer text-zinc-400">原始响应</summary>
                          <pre className="whitespace-pre-wrap text-zinc-300 mt-2 max-h-64 overflow-auto">{a.raw_text}</pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </Block>
            )}

            {log.thinking && (
              <Block icon={<Brain className="h-4 w-4" />} title="思考过程 (extended thinking)" hint="模型在产出最终答案前的内部推理。仅 Claude 等支持 extended thinking 的模型有内容。">
                <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-[600px] overflow-auto">{log.thinking}</pre>
              </Block>
            )}

            <Block icon={<MessageSquare className="h-4 w-4" />} title="System Prompt" hint="发给模型的系统提示。">
              <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded">{log.system_prompt || '—'}</pre>
            </Block>

            <Block icon={<FileJson className="h-4 w-4" />} title="用户输入 (User Input)" hint="作为 user message 发给模型的 JSON 数据。">
              <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-[600px] overflow-auto">{log.user_input ? JSON.stringify(log.user_input, null, 2) : '—'}</pre>
            </Block>

            <Block icon={<Code2 className="h-4 w-4" />} title="原始响应文本 (Raw)" hint="模型返回的原始字符串，未经 JSON 解析、未经 schema 校验。">
              <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-[600px] overflow-auto">{log.raw_response_text || '—'}</pre>
            </Block>

            <Block icon={<FileJson className="h-4 w-4" />} title="解析后的结构化输出 (Parsed)" hint="经过 Pydantic schema 校验后的 JSON。这是业务侧实际使用的内容。">
              <pre className="whitespace-pre-wrap text-xs text-zinc-300 bg-zinc-950 p-3 rounded max-h-[600px] overflow-auto">{log.response_payload ? JSON.stringify(log.response_payload, null, 2) : '—'}</pre>
            </Block>
          </>
        )
      }
    </div>
  );
}

function Stat({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="bg-zinc-950 p-2 rounded">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={mono ? 'font-mono text-xs mt-1' : 'mt-1'}>{value}</div>
    </div>
  );
}

function Block({
  icon,
  title,
  hint,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          {icon} {title}
        </CardTitle>
        <CardDescription>{hint}</CardDescription>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
