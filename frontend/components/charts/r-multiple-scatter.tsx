'use client';

import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { TradeRow } from '@/lib/types';

interface Props {
  trades: TradeRow[];
  height?: number;
}

export function RMultipleScatter({ trades, height = 250 }: Props) {
  const data = trades
    .filter((t) => t.realized_r_multiple !== null && t.exit_time)
    .map((t) => ({
      x: new Date(t.exit_time as string).getTime(),
      y: Number(t.realized_r_multiple),
      symbol: t.symbol,
      reason: t.exit_reason,
    }));

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-zinc-500 text-sm"
        style={{ height }}
      >
        无已平仓交易数据
      </div>
    );
  }

  const positives = data.filter((d) => d.y > 0);
  const negatives = data.filter((d) => d.y <= 0);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          type="number"
          dataKey="x"
          stroke="#71717a"
          fontSize={11}
          domain={['auto', 'auto']}
          tickFormatter={(v: number) =>
            new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
          }
        />
        <YAxis
          type="number"
          dataKey="y"
          stroke="#71717a"
          fontSize={11}
          tickFormatter={(v: number) => `${v.toFixed(1)}R`}
        />
        <ReferenceLine y={0} stroke="#52525b" />
        <Tooltip
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid #3f3f46',
            borderRadius: '6px',
          }}
          formatter={(_value: number, _name: string, item: { payload?: { y: number; symbol: string; reason: string | null } }) => {
            const p = item.payload;
            if (!p) return ['—', ''];
            return [`${p.y.toFixed(2)}R · ${p.symbol} · ${p.reason ?? '—'}`, ''];
          }}
          labelFormatter={(value: number) =>
            new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
          }
        />
        <Scatter data={positives} fill="#22c55e" />
        <Scatter data={negatives} fill="#ef4444" />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
