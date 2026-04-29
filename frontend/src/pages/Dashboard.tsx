import { useQuery } from "@tanstack/react-query";
import { getDashboardStats } from "../lib/api";
import Card from "../components/ui/Card";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboardStats,
  });

  if (isLoading) {
    return <div className="p-8">加载中...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-400">加载失败</div>;
  }

  const stats = data || {
    total_projects: 0,
    total_word_count: 0,
    total_chapters: 0,
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">数据看板</h1>
        <p className="text-gray-400">总览你的创作进展</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="项目总数" value={stats.total_projects.toString()} icon="📚" />
        <Card title="总字数" value={stats.total_word_count.toLocaleString() + " 字"} icon="📝" />
        <Card title="总章节数" value={stats.total_chapters.toString() + " 章"} icon="📖" />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-white mb-3">近期写作量</h2>
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-gray-400">（此功能待实现）</p>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-white mb-3">各项目进度</h2>
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-gray-400">（此功能待实现）</p>
        </div>
      </div>
    </div>
  );
}
