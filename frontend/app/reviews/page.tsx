'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Reviews() {
  const { data: reviews } = useSWR<any[]>('/api/reviews?limit=50', fetcher);

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">复盘</h1>
      <div className="space-y-3">
        {reviews?.map((r) => (
          <div key={r.id} className="p-4 bg-zinc-900 rounded border border-zinc-800">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-zinc-400">trade_id={r.trade_id}</span>
              <span className="text-zinc-500 text-xs">{new Date(r.created_at).toLocaleString()}</span>
            </div>
            <div className="text-sm whitespace-pre-wrap mb-3">{r.summary}</div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <span className="bg-zinc-950 px-2 py-1 rounded">入场质量 {r.entry_quality}/5</span>
              <span className="bg-zinc-950 px-2 py-1 rounded">出场质量 {r.exit_quality}/5</span>
              <span className="bg-zinc-950 px-2 py-1 rounded">风控 {r.risk_control_quality}/5</span>
            </div>
            {r.what_failed?.length > 0 && (
              <div className="mt-3 text-xs">
                <div className="text-red-400 mb-1">失败:</div>
                <ul className="list-disc list-inside text-zinc-400">
                  {r.what_failed.map((s: string, i: number) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
      {(!reviews || reviews.length === 0) && <p className="text-zinc-500 text-sm">尚无复盘。</p>}
    </div>
  );
}
