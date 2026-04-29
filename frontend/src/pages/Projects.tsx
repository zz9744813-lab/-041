import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProjects, createProject, deleteProject } from "../lib/api";
import Card from "../components/ui/Card";
import Modal from "../components/ui/Modal";
import Button from "../components/ui/Button";

export default function Projects() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newType, setNewType] = useState("novel");

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  const createMutation = useMutation({
    mutationFn: () => createProject({ title: newTitle, type: newType, description: newDescription }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowModal(false);
      setNewTitle("");
      setNewDescription("");
      setNewType("novel");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });

  const handleCreate = () => {
    if (!newTitle.trim()) return;
    createMutation.mutate();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">我的项目</h1>
          <p className="text-gray-400">管理你的小说、短篇、随笔</p>
        </div>
        <Button onClick={() => setShowModal(true)}>+ 新建项目</Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">加载项目...</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12 text-gray-400 border border-dashed border-[var(--border)] rounded-xl">
          <div className="text-5xl mb-4">📚</div>
          <p className="text-lg">尚无项目</p>
          <p className="text-sm mt-2">点击右上角按钮开始创作</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <div
              key={p.id}
              className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-5 transition-colors hover:bg-[#282828] cursor-pointer"
              onClick={() => window.location.href = \`/projects/\${p.id}\`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs px-2 py-1 rounded-full bg-indigo-900/30 text-indigo-300">
                  {p.type === "novel" ? "长篇小说" : p.type === "short" ? "短篇" : "随笔"}
                </span>
                <span className="text-xs text-gray-400">{p.chapter_count} 章</span>
              </div>
              <h3 className="text-lg font-semibold text-white mt-3 mb-1">{p.title}</h3>
              <p className="text-sm text-gray-400 line-clamp-2">{p.description || "无描述"}</p>
              <div className="flex items-center justify-between mt-4">
                <span className="text-sm text-gray-300">{p.word_count.toLocaleString()} 字</span>
                <span className="text-xs text-gray-500">
                  {new Date(p.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} title="新建项目">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">标题</label>
            <input
              type="text"
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="例如：《我的第一部小说》"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">类型</label>
            <select
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white"
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
            >
              <option value="novel">长篇小说</option>
              <option value="short">短篇创作</option>
              <option value="essay">随笔杂记</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">描述</label>
            <textarea
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white"
              rows={3}
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="简单介绍一下你的作品..."
            />
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              取消
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newTitle.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? "创建中..." : "确认创建"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
