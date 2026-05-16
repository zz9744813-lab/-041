'use client';

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import type { DrawdownPoint } from '@/lib/types';

interface Props {
  data: DrawdownPoint[];
  height?: number;
}

export function DrawdownChart({ data, height = 200 }: Props) {
  const formatted = data.map((d) => ({
    ts: new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    drawdown: -Number(d.drawdown_pct) * 100, // negative for visual
  }));

  if (formatted.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-zinc-500 text-sm"
        style={{ height }}
      >
        无数据
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0.4} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis dataKey="ts" stroke="#71717a" fontSize={11} />
        <YAxis
          stroke="#71717a"
          fontSize={11}
          tickFormatter={(v: number) => `${v.toFixed(1)}%`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid #3f3f46',
            borderRadius: '6px',
          }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(value: number) => `${value.toFixed(2)}%`}
        />
        <Area
          type="monotone"
          dataKey="drawdown"
          stroke="#ef4444"
          strokeWidth={1.5}
          fill="url(#ddGrad)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
