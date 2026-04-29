import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getChapter, updateChapter } from "../lib/api";

export default function Editor() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId: string }>();
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("draft");
  const [synopsis, setSynopsis] = useState("");
  const [notes, setNotes] = useState("");
  const [pov, setPov] = useState("");
  const [characters, setCharacters] = useState("");
  const [locations, setLocations] = useState("");
  const [saved, setSaved] = useState(true);
  const [saving, setSaving] = useState(false);

  const { data: chapter, isLoading } = useQuery({
    queryKey: ["chapter", projectId, chapterId],
    queryFn: () => getChapter(projectId!, chapterId!),
    enabled: !!projectId && !!chapterId,
    onSuccess: (data) => {
      if (data) {
        setTitle(data.title);
        setStatus(data.status);
        setSynopsis(data.synopsis || "");
        setNotes(data.notes || "");
        setPov(data.pov || "");
        setCharacters(data.characters || "");
        setLocations(data.locations || "");
        setContent(data.content || "");
        setSaved(true);
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => updateChapter(projectId!, chapterId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] });
      setSaved(true);
      setSaving(false);
    },
    onError: () => setSaving(false),
  });

  const handleSave = async () => {
    setSaving(true);
    updateMutation.mutate({
      title,
      status,
      synopsis,
      notes,
      pov,
      characters,
      locations,
      content,
      word_count: content.trim().split(/\s+/).length,
    });
  };

  // Auto-save timer
  useEffect(() => {
    if (!saved && content !== (chapter?.content || "")) {
      const timer = setTimeout(() => handleSave(), 30000); // 30s auto-save
      return () => clearTimeout(timer);
    }
  }, [content, saved]);

  // Keyboard shortcut Ctrl+S
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [content, title, status]);

  if (isLoading) {
    return <div className="p-8 text-gray-400">加载章节...</div>;
  }

  return (
    <div className="flex h-screen bg-[var(--bg-primary)]">
      {/* Left sidebar - chapter list (minimal for now) */}
      <div className="w-64 border-r border-[var(--border)] p-4">
        <h2 className="font-medium text-white mb-4">章节</h2>
        <div className="text-gray-400 text-sm">（章节列表占位）</div>
      </div>

      {/* Main editor */}
      <div className="flex-1 flex flex-col">
        {/* Editor header */}
        <header className="border-b border-[var(--border)] px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <input
              type="text"
              className="text-xl font-semibold bg-transparent border-none text-white w-96"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setSaved(false);
              }}
              placeholder="章节标题"
            />
            <select
              className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-1 text-sm text-white"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setSaved(false);
              }}
            >
              <option value="draft">草稿</option>
              <option value="wip">进行中</option>
              <option value="review">待修订</option>
              <option value="done">已完成</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400">
              {content.trim().split(/\s+/).length} 字
            </span>
            <button
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium disabled:opacity-50"
              onClick={handleSave}
              disabled={saving || saved}
            >
              {saving ? "保存中..." : saved ? "已保存" : "保存"}
            </button>
          </div>
        </header>

        {/* Text area */}
        <div className="flex-1 p.
</div>
        <textarea
          className="w-full h-full bg-transparent text-white p-6 resize-none outline-none text-lg leading-relaxed"
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setSaved(false);
          }}
          placeholder="开始写作..."
          spellCheck="false"
        />
      </div>

      {/* Right sidebar - metadata */}
      <div className="w-80 border-l border-[var(--border)] p-6 space-y-6">
        <div>
          <h3 className="font-medium text-white mb-2">摘要</h3>
          <textarea
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm"
            rows={3}
            value={synopsis}
            onChange={(e) => {
              setSynopsis(e.target.value);
              setSaved(false);
            }}
            placeholder="本章节的主要内容..."
          />
        </div>
        <div>
          <h3 className="font-medium text-white mb-2">备注</h3>
          <textarea
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm"
            rows={3}
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              setSaved(false);
            }}
            placeholder="作者的私人笔记..."
          />
        </div>
        <div>
          <h3 className="font-medium text-white mb-2">视角 (POV)</h3>
          <input
            type="text"
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm"
            value={pov}
            onChange={(e) => {
              setPov(e.target.value);
              setSaved(false);
            }}
            placeholder="第一人称/第三人称/上帝视角"
          />
        </div>
        <div>
          <h3 className="font-medium text-white mb-2">出场角色</h3>
          <input
            type="text"
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm"
            value={characters}
            onChange={(e) => {
              setCharacters(e.target.value);
              setSaved(false);
            }}
            placeholder="张三, 李四, 王五"
          />
        </div>
        <div>
          <h3 className="font-medium text-white mb-2">地点</h3>
          <input
            type="text"
            className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm"
            value={locations}
            onChange={(e) => {
              setLocations(e.target.value);
              setSaved(false);
            }}
            placeholder="书房, 森林, 城堡"
          />
        </div>
      </div>
    </div>
  );
}
