'use client';

import {
  Activity,
  BarChart3,
  Briefcase,
  History,
  Home,
  ListChecks,
  ScrollText,
  Settings,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

const NAV = [
  { href: '/', label: '首页', icon: Home },
  { href: '/watchlist', label: '观察池', icon: ListChecks },
  { href: '/signals', label: '信号', icon: TrendingUp },
  { href: '/positions', label: '持仓', icon: Briefcase },
  { href: '/trades', label: '交易', icon: History },
  { href: '/models', label: '模型', icon: BarChart3 },
  { href: '/reviews', label: '复盘', icon: ScrollText },
  { href: '/system', label: '系统', icon: Settings },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-30 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
      <div className="max-w-7xl mx-auto px-6 h-12 flex items-center gap-1 overflow-x-auto">
        <Link href="/" className="text-sm font-bold text-zinc-100 mr-4 whitespace-nowrap flex items-center gap-1">
          <Activity className="h-4 w-4" /> Mini Hermes
        </Link>
        {NAV.map((n) => {
          const active = n.href === '/' ? pathname === '/' : pathname?.startsWith(n.href);
          const Icon = n.icon;
          return (
            <Link
              key={n.href}
              href={n.href}
              className={cn(
                'px-3 py-1.5 text-sm rounded flex items-center gap-1.5 whitespace-nowrap transition-colors',
                active
                  ? 'bg-zinc-100 text-zinc-900'
                  : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100',
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {n.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
