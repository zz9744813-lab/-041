import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getProject, getChapters, getCharacters, getWorldItems,
  deleteChapter, createChapter,
  generateSetting, generateOutline, generateAll,
  startAutogen, pauseAutogen, resumeAutogen, stopAutogen, getAutogenStatus,
} from "../lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"chapters" | "characters" | "world">("chapters");
  const [showChapterModal, setShowChapterModal] = useState(false);
  const [newChapter, setNewChapter] = useState({ title: "", outline: "", target_words: 2000 });
  const [genStatus, setGenStatus] = useState<string | null>(null);

  const { data: project, refetch: refetchProject } = useQuery({
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

  // ─── Autogen status polling ───
  const { data: autogenStatus, refetch: refetchAutogen } = useQuery({
    queryKey: ["autogen", projectId],
    queryFn: () => getAutogenStatus(projectId!),
    enabled: !!projectId,
    refetchInterval: (data) => (data?.running ? 3000 : false),
  });

  // ─── Mutations ───
  const deleteChapterMutation = useMutation({
    mutationFn: (cid: string) => deleteChapter(projectId!, cid),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["chapters", projectId] }); refetchProject(); },
  });

  const createChapterMutation = useMutation({
    mutationFn: () => createChapter(projectId!, newChapter),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapters", projectId] });
      setShowChapterModal(false);
      setNewChapter({ title: "", outline: "", target_words: 2000 });
    },
  });

  const genSettingMutation = useMutation({
    mutationFn: () => generateSetting(projectId!),
    onSuccess: () => { setGenStatus("设定生成完成!"); refetchProject(); setTimeout(() => setGenStatus(null), 3000); },
    onError: (e: any) => { setGenStatus(`生成失败: ${e?.response?.data?.detail || e.message}`); },
  });

  const genOutlineMutation = useMutation({
    mutationFn: () => generateOutline(projectId!),
    onSuccess: () => { setGenStatus("大纲生成完成!"); refetchProject(); setTimeout(() => setGenStatus(null), 3000); },
    onError: (e: any) => { setGenStatus(`生成失败: ${e?.response?.data?.detail || e.message}`); },
  });

  const genAllMutation = useMutation({
    mutationFn: () => generateAll(projectId!),
    onSuccess: () => { setGenStatus("设定+大纲生成完成!"); refetchProject(); setTimeout(() => setGenStatus(null), 3000); },
    onError: (e: any) => { setGenStatus(`生成失败: ${e?.response?.data?.detail || e.message}`); },
  });

  const autogenStartMutation = useMutation({
    mutationFn: () => startAutogen(projectId!),
    onSuccess: () => { refetchAutogen(); },
    onError: (e: any) => { setGenStatus(`自主生成启动失败: ${e?.response?.data?.detail || e.message}`); },
  });

  const autogenPauseMutation = useMutation({
    mutationFn: () => pauseAutogen(projectId!),
    onSuccess: () => { refetchAutogen(); },
  });

  const autogenResumeMutation = useMutation({
    mutationFn: () => resumeAutogen(projectId!),
    onSuccess: () => { refetchAutogen(); },
  });

  const autogenStopMutation = useMutation({
    mutationFn: () => stopAutogen(projectId!),
    onSuccess: () => { refetchAutogen(); },
  });

  const isAutogenRunning = autogenStatus?.running || false;
  const isAutogenPaused = autogenStatus?.status === "paused";
  const autogenProgress = autogenStatus?.progress || 0;

  if (!project) {
    return <div className="p-8 text-gray-400">加载中...</div>;
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">{project.title}</h1>
          <div className="flex items-center gap-2">
            <span className="text-sm px-2 py-1 rounded-full bg-gray-900/50 text-gray-400">{project.type}</span>
            <span className="text-sm px-2 py-1 rounded-full bg-indigo-900/30 text-indigo-300">{project.status}</span>
          </div>
        </div>
        <p className="text-gray-400 mt-1 text-sm">{project.idea && `💡 ${project.idea}`}</p>
        {project.genre && <p className="text-gray-500 text-xs mt-1">题材: {project.genre} · 风格: {project.style} · 目标: {project.target_words}字</p>}

        {/* Status notification */}
        {genStatus && (
          <div className="mt-2 px-3 py-2 rounded-lg bg-indigo-900/30 text-indigo-300 text-sm border border-indigo-700/30">
            {genStatus}
          </div>
        )}

        {/* Autogen progress */}
        {isAutogenRunning && (
          <div className="mt-2 px-3 py-2 rounded-lg bg-green-900/30 text-green-300 text-sm border border-green-700/30">
            📝 自主生成中... 第{autogenStatus?.current_chapter}章 | 完成{autogenStatus?.completed_chapters}/{autogenStatus?.total_chapters}章
            <div className="w-full h-2 bg-gray-800 rounded-full mt-1">
              <div className="h-full bg-green-500 rounded-full transition-all" style={{ width: `${autogenProgress}%` }} />
            </div>
          </div>
        )}
        {isAutogenPaused && (
          <div className="mt-2 px-3 py-2 rounded-lg bg-yellow-900/30 text-yellow-300 text-sm border border-yellow-700/30">
            ⏸️ 自主生成已暂停
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-wrap items-center gap-2 mt-4">
          <Link to={`/projects/${projectId}/editor`}>
            <Button variant="primary">✍️ 进入写作台</Button>
          </Link>
          <Button
            variant="secondary"
            onClick={() => genSettingMutation.mutate()}
            disabled={genSettingMutation.isPending || !project.idea}
          >
            {genSettingMutation.isPending ? "生成中..." : "📖 生成设定"}
          </Button>
          <Button
            variant="secondary"
            onClick={() => genOutlineMutation.mutate()}
            disabled={genOutlineMutation.isPending || project.status === "idea"}
          >
            {genOutlineMutation.isPending ? "生成中..." : "📋 生成大纲"}
          </Button>
          <Button
            variant="secondary"
            onClick={() => genAllMutation.mutate()}
            disabled={genAllMutation.isPending}
          >
            {genAllMutation.isPending ? "生成中..." : "🚀 生成设定+大纲"}
          </Button>

          <div className="w-px h-6 bg-gray-700 mx-1" />

          {!isAutogenRunning && !isAutogenPaused && (
            <Button
              variant="secondary"
              onClick={() => autogenStartMutation.mutate()}
              disabled={autogenStartMutation.isPending || chapters.length === 0}
            >
              {autogenStartMutation.isPending ? "启动中..." : "▶️ 自主生成"}
            </Button>
          )}
          {isAutogenRunning && (
            <Button variant="secondary" onClick={() => autogenPauseMutation.mutate()}>⏸️ 暂停</Button>
          )}
          {isAutogenPaused && (
            <Button variant="secondary" onClick={() => autogenResumeMutation.mutate()}>▶️ 继续</Button>
          )}
          {(isAutogenRunning || isAutogenPaused) && (
            <Button variant="secondary" onClick={() => autogenStopMutation.mutate()} className="text-red-400 hover:bg-red-900/20">⏹️ 停止</Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--border)] mb-6">
        {(["chapters", "characters", "world"] as const).map((tab) => (
          <button
            key={tab}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "text-indigo-300 border-b-2 border-indigo-500"
                : "text-gray-400 hover:text-gray-300"
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "chapters" ? "📖 章节" : tab === "characters" ? "👤 角色" : "🌍 世界观"}
          </button>
        ))}
      </div>

      {/* Chapters Tab */}
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
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        ch.status === "generated" ? "bg-green-900/30 text-green-300" :
                        ch.status === "generating" ? "bg-yellow-900/30 text-yellow-300" :
                        ch.status === "failed" ? "bg-red-900/30 text-red-300" :
                        "bg-gray-800 text-gray-400"
                      }`}>
                        {ch.status}
                      </span>
                    </div>
                    {ch.outline && <p className="text-sm text-gray-500 mt-1 truncate max-w-md">{ch.outline}</p>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-300">{ch.actual_words || ch.word_count} 字</span>
                    <Link to={`/projects/${projectId}/chapters/${ch.id}/edit`}>
                      <Button variant="secondary">编辑</Button>
                    </Link>
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

      {/* Characters Tab */}
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

      {/* World Tab */}
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
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-900/50 text-gray-400">{item.category}</span>
                  </div>
                  <p className="text-sm text-gray-300 mt-2 line-clamp-3">{item.content || "无内容"}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Chapter Modal */}
      <Modal open={showChapterModal} onClose={() => setShowChapterModal(false)} title="新建章节">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">章节标题</label>
            <input
              type="text"
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white"
              value={newChapter.title}
              onChange={(e) => setNewChapter({ ...newChapter, title: e.target.value })}
              placeholder="例如：第一章 起点"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">章节大纲（可选）</label>
            <textarea
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm"
              rows={3}
              value={newChapter.outline}
              onChange={(e) => setNewChapter({ ...newChapter, outline: e.target.value })}
              placeholder="本章主要发生什么..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">目标字数</label>
            <input
              type="number"
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white"
              value={newChapter.target_words}
              onChange={(e) => setNewChapter({ ...newChapter, target_words: parseInt(e.target.value) || 2000 })}
            />
          </div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowChapterModal(false)}>取消</Button>
            <Button onClick={() => createChapterMutation.mutate()} disabled={!newChapter.title.trim() || createChapterMutation.isPending}>
              {createChapterMutation.isPending ? "创建中..." : "确认创建"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}