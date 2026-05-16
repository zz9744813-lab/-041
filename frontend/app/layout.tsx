import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Mini Hermes',
  description: 'AI 模拟交易与策略验证系统',
};

const NAV = [
  { href: '/', label: '首页' },
  { href: '/watchlist', label: '观察池' },
  { href: '/signals', label: '信号' },
  { href: '/positions', label: '持仓' },
  { href: '/trades', label: '交易' },
  { href: '/models', label: '模型' },
  { href: '/reviews', label: '复盘' },
  { href: '/system', label: '系统' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen flex flex-col">
        <nav className="sticky top-0 z-30 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
          <div className="max-w-7xl mx-auto px-6 h-12 flex items-center gap-1 overflow-x-auto">
            <span className="text-sm font-bold text-zinc-100 mr-4 whitespace-nowrap">Mini Hermes</span>
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className="px-3 py-1 text-sm rounded text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100 whitespace-nowrap"
              >
                {n.label}
              </Link>
            ))}
          </div>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
