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

import type { EquityCurvePoint } from '@/lib/types';

interface Props {
  data: EquityCurvePoint[];
  height?: number;
}

export function EquityCurveChart({ data, height = 200 }: Props) {
  const formatted = data.map((d) => ({
    ts: new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    equity: Number(d.equity),
  }));

  if (formatted.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-zinc-500 text-sm"
        style={{ height }}
      >
        无数据。先生成几个 PortfolioSnapshot。
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis dataKey="ts" stroke="#71717a" fontSize={11} />
        <YAxis
          stroke="#71717a"
          fontSize={11}
          domain={['auto', 'auto']}
          tickFormatter={(v: number) => `$${v.toLocaleString()}`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#18181b',
            border: '1px solid #3f3f46',
            borderRadius: '6px',
          }}
          labelStyle={{ color: '#a1a1aa' }}
          formatter={(value: number) => `$${value.toLocaleString()}`}
        />
        <Area
          type="monotone"
          dataKey="equity"
          stroke="#22c55e"
          strokeWidth={1.5}
          fill="url(#equityGrad)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
