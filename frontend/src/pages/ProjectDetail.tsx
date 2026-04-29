import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProject, getChapters, getCharacters, getWorldItems, deleteChapter } from "../lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"chapters" | "characters" | "world">("chapters");
  const [showChapterModal, setShowChapterModal] = useState(false);
  const [newChapterTitle, setNewChapterTitle] = useState("");

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });

  const { data: chapters = [] } = useQuery({
    queryKey: ["chapters", projectId],
    queryFn: () => getChapters(projectId!),
    enabled: !!projectId && activeTab === "chapters",
  });

  const { data: characters = [] } = useQuery({
    queryKey: ["characters", projectId],
    queryFn: () => getCharacters(projectId!),
    enabled: !!projectId && activeTab === "characters",
  });

  const { data: worldItems = [] } = useQuery({
    queryKey: ["worldItems", projectId],
    queryFn: () => getWorldItems(projectId!),
    enabled: !!projectId && activeTab === "world",
  });

  const deleteChapterMutation = useMutation({
    mutationFn: (chapterId: string) => deleteChapter(projectId!, chapterId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chapters", projectId] }),
  });

  if (!project) {
    return <div className="p-8 text-gray-400">加载中...</div>;
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">{project.title}</h1>
          <div className="text-sm text-gray-400">{project.type} · {project.status}</div>
        </div>
        <p className="text-gray-400 mt-2">{project.description}</p>
        <div className="flex items-center gap-4 mt-4">
          <Button onClick={() => window.location.href = \`/projects/\${projectId}/editor?\`} variant="primary">
            进入写作台
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--border)] mb-6">
        {["chapters", "characters", "world"].map((tab) => (
          <button
            key={tab}
            className={\`px-4 py-2 text-sm font-medium transition-colors \${
              activeTab === tab
                ? "text-indigo-300 border-b-2 border-indigo-500"
                : "text-gray-400 hover:text-gray-300"
            }\`}
            onClick={() => setActiveTab(tab as any)}
          >
            {tab === "chapters" ? "📖 章节" : tab === "characters" ? "👤 角色" : "🌍 世界观"}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === "chapters" && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">章节列表</h2>
            <Button onClick={() => setShowChapterModal(true)}>+ 新建章节</Button>
          </div>
          {chapters.length === 0 ? (
            <div className="text-center py-8 text-gray-400 border border-dashed border-[var(--border)] rounded-xl">
              尚无章节
            </div>
          ) : (
            <div className="space-y-2">
              {chapters.map((ch) => (
                <div
                  key={ch.id}
                  className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4 flex items-center justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-gray-500 w-6">#{ch.chapter_number}</span>
                      <h3 className="font-medium text-white">{ch.title}</h3>
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-900/50 text-gray-400">
                        {ch.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{ch.notes || "无备注"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-300">{ch.word_count} 字</span>
                    <Button
                      variant="secondary"
                      onClick={() => window.location.href = \`/projects/\${projectId}/chapters/\${ch.id}/edit\`}
                    >
                      编辑
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => deleteChapterMutation.mutate(ch.id)}
                      className="text-red-400 hover:bg-red-900/20"
                    >
                      删除
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "characters" && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">角色设定</h2>
          {characters.length === 0 ? (
            <div className="text-center py-8 text-gray-400">尚无角色</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {characters.map((ch) => (
                <div key={ch.id} className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4">
                  <h3 className="font-semibold text-white">{ch.name}</h3>
                  <p className="text-sm text-gray-400">{ch.age} · {ch.gender}</p>
                  <p className="text-sm text-gray-300 mt-2 line-clamp-3">{ch.personality}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "world" && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">世界观</h2>
          {worldItems.length === 0 ? (
            <div className="text-center py-8 text-gray-400">尚无世界观条目</div>
          ) : (
            <div className="space-y-3">
              {worldItems.map((item) => (
                <div key={item.id} className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-white">{item.title}</h3>
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-900/50 text-gray-400">
                      {item.category}
                    </span>
                  </div>
                  <p className="text-sm text-gray-300 mt-2 line-clamp-3">{item.content || "无内容"}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <Modal open={showChapterModal} onClose={() => setShowChapterModal(false)} title="新建章节">
        <div className="space-y-4">
          <p className="text-gray-400 text-sm">章节创建后可在写作台中编辑内容。</p>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">章节标题</label>
            <input
              type="text"
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white"
              value={newChapterTitle}
              onChange={(e) => setNewChapterTitle(e.target.value)}
              placeholder="例如：第一章 起点"
              autoFocus
            />
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowChapterModal(false)}>
              取消
            </Button>
            <Button onClick={() => {}} disabled={!newChapterTitle.trim()}>
              确认创建
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
