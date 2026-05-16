import './globals.css';
import type { Metadata } from 'next';

import { TopNav } from '@/components/top-nav';

export const metadata: Metadata = {
  title: 'Mini Hermes',
  description: 'AI 模拟交易与策略验证系统',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen flex flex-col">
        <TopNav />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
