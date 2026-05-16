'use client';

import { Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Briefcase } from 'lucide-react';
import useSWR from 'swr';

import { DrawdownChart } from '@/components/charts/drawdown';
import { EquityCurveChart } from '@/components/charts/equity-curve';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/states';
import { fetcher } from '@/lib/fetcher';
import type {
  DrawdownPoint,
  EquityCurvePoint,
  PortfolioSnapshot,
  RegimeRow,
  SignalRow,
  SystemHealthRow,
} from '@/lib/types';
import { cn, fmt, fmtPct } from '@/lib/utils';

function regimeColor(regime: string | null | undefined): 'success' | 'warning' | 'danger' | 'muted' {
  if (!regime) return 'muted';
  if (regime.includes('STRONG_BULL') || regime.includes('MILD_BULL')) return 'success';
  if (regime === 'RANGE') return 'muted';
  if (regime.includes('PANIC') || regime.includes('STRONG_BEAR')) return 'danger';
  return 'warning';
}

export default function Home() {
  const portfolioR = useSWR<PortfolioSnapshot | null>('/api/portfolio', fetcher, {
    refreshInterval: 30000,
  });
  const regimeR = useSWR<RegimeRow>('/api/market/regime', fetcher, { refreshInterval: 60000 });
  const signalsR = useSWR<SignalRow[]>('/api/signals?limit=10', fetcher, { refreshInterval: 30000 });
  const equityR = useSWR<EquityCurvePoint[]>('/api/portfolio/equity-curve?days=30', fetcher);
  const drawdownR = useSWR<DrawdownPoint[]>('/api/portfolio/drawdown?days=30', fetcher);
  const healthR = useSWR<SystemHealthRow[]>('/api/system/health', fetcher, { refreshInterval: 60000 });

  const portfolio = portfolioR.data ?? null;
  const totalReturn = portfolio ? Number(portfolio.total_return_pct) : 0;
  const drawdownPct = portfolio ? Number(portfolio.max_drawdown_pct) : 0;
  const recentFailed = (healthR.data ?? []).filter((h) => h.status === 'FAILED').length;
  const llmFailureBanner = recentFailed >= 2;
  const drawdownBanner = drawdownPct >= 0.05;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {(llmFailureBanner || drawdownBanner) && (
        <div className="rounded-lg border border-yellow-700 bg-yellow-900/20 p-3 text-sm flex items-center gap-2 text-yellow-300">
          <AlertTriangle className="h-4 w-4" />
          <span>
            {drawdownBanner && `账户回撤 ${(drawdownPct * 100).toFixed(2)}% 已超 5%；`}
            {llmFailureBanner && `近期任务失败 ${recentFailed} 次。`}
            前往 <a className="underline" href="/system">/system</a> 查看详情。
          </span>
        </div>
      )}

      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Mini Hermes Dashboard</h1>
        <Badge variant={regimeColor(regimeR.data?.regime)}>
          {regimeR.data?.regime ?? 'REGIME_PENDING'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          label="账户净值"
          value={portfolio ? `$${fmt(portfolio.equity)}` : portfolioR.error ? 'API 错误' : '加载中'}
          icon={<Briefcase className="h-4 w-4 text-zinc-500" />}
        />
        <KpiCard
          label="累计收益"
          value={portfolio ? fmtPct(totalReturn) : '—'}
          tone={totalReturn > 0 ? 'up' : totalReturn < 0 ? 'down' : 'flat'}
          icon={
            totalReturn > 0 ? (
              <ArrowUpRight className="h-4 w-4 text-green-400" />
            ) : (
              <ArrowDownRight className="h-4 w-4 text-red-400" />
            )
          }
        />
        <KpiCard
          label="最大回撤"
          value={portfolio ? fmtPct(drawdownPct) : '—'}
          tone="down"
          icon={<AlertTriangle className="h-4 w-4 text-red-400" />}
        />
        <KpiCard
          label="持仓数 / 连续亏损"
          value={
            portfolio
              ? `${portfolio.open_positions_count} / ${portfolio.consecutive_losses}`
              : '—'
          }
          icon={<Activity className="h-4 w-4 text-zinc-500" />}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>账户净值 (近 30 日)</CardTitle>
            <CardDescription>每日 PortfolioSnapshot 累计</CardDescription>
          </CardHeader>
          <CardContent>
            {equityR.error ? (
              <ErrorState error={equityR.error} />
            ) : !equityR.data ? (
              <LoadingState />
            ) : equityR.data.length === 0 ? (
              <EmptyState
                message="无 PortfolioSnapshot"
                hint="运行 daily_report_job 后生成"
              />
            ) : (
              <EquityCurveChart data={equityR.data} />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>回撤曲线</CardTitle>
            <CardDescription>峰值至当前的相对跌幅</CardDescription>
          </CardHeader>
          <CardContent>
            {drawdownR.error ? (
              <ErrorState error={drawdownR.error} />
            ) : !drawdownR.data ? (
              <LoadingState />
            ) : drawdownR.data.length === 0 ? (
              <EmptyState message="无回撤数据" />
            ) : (
              <DrawdownChart data={drawdownR.data} />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>最近信号</CardTitle>
          <CardDescription>新的策略输出 + AI 修正</CardDescription>
        </CardHeader>
        <CardContent>
          {signalsR.error ? (
            <ErrorState error={signalsR.error} height={120} />
          ) : !signalsR.data ? (
            <LoadingState height={120} />
          ) : signalsR.data.length === 0 ? (
            <EmptyState
              height={120}
              message="暂无信号"
              hint={
                <>
                  运行 <code>python -m app.scheduler</code> 或调用{' '}
                  <code>POST /api/signals/run</code>
                </>
              }
            />
          ) : (
            <ul className="text-sm space-y-1.5">
              {signalsR.data.slice(0, 10).map((s) => (
                <li key={s.id} className="flex justify-between items-center">
                  <span className="flex items-center gap-2">
                    <span className="font-mono">{s.symbol}</span>
                    <Badge variant="muted">{s.signal_type}</Badge>
                    <span className="text-zinc-400 text-xs">conf={s.confidence_score}</span>
                  </span>
                  <Badge variant={signalStatusVariant(s.status)}>{s.status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function signalStatusVariant(
  status: string,
): 'success' | 'warning' | 'danger' | 'info' | 'muted' {
  if (status === 'EXECUTED') return 'success';
  if (status === 'APPROVED' || status === 'APPROVED_WAITING_ENTRY') return 'info';
  if (status === 'REJECTED') return 'danger';
  if (status === 'EXPIRED' || status === 'SUPERSEDED') return 'muted';
  return 'warning';
}

function KpiCard({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: string;
  tone?: 'up' | 'down' | 'flat';
  icon?: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <div className="flex items-center justify-between">
          <CardDescription>{label}</CardDescription>
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div
          className={cn(
            'text-2xl font-bold font-mono',
            tone === 'up' && 'text-green-400',
            tone === 'down' && 'text-red-400',
          )}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
