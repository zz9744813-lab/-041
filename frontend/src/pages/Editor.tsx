import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getChapter, updateChapter,
  getChapterVersions, setCurrentVersion,
  generateChapter, continueChapter, reviseChapter, checkConsistency,
  getChapters,
} from "../lib/api";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";

export default function Editor() {
  const { projectId, chapterId } = useParams<{ projectId: string; chapterId: string }>();
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [status, setStatus] = useState("planned");
  const [synopsis, setSynopsis] = useState("");
  const [notes, setNotes] = useState("");
  const [pov, setPov] = useState("");
  const [characters, setCharacters] = useState("");
  const [locations, setLocations] = useState("");
  const [outline, setOutline] = useState("");
  const [saved, setSaved] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [showGenModal, setShowGenModal] = useState(false);
  const [showContinueModal, setShowContinueModal] = useState(false);
  const [showReviseModal, setShowReviseModal] = useState(false);
  const [showVersionsModal, setShowVersionsModal] = useState(false);
  const [promptText, setPromptText] = useState("");

  const showMsg = (msg: string) => { setStatusMsg(msg); setTimeout(() => setStatusMsg(null), 4000); };

  const { data: chapter, isLoading } = useQuery({
    queryKey: ["chapter", projectId, chapterId],
    queryFn: () => getChapter(projectId!, chapterId!),
    enabled: !!projectId && !!chapterId,
  });

  useEffect(() => {
    if (chapter) {
      setTitle(chapter.title || "");
      setStatus(chapter.status || "planned");
      setSynopsis(chapter.synopsis || "");
      setNotes(chapter.notes || "");
      setPov(chapter.pov || "");
      setCharacters(chapter.characters || "");
      setLocations(chapter.locations || "");
      setOutline(chapter.outline || "");
      setContent(chapter.content || "");
      setSaved(true);
    }
  }, [chapter]);

  const { data: chapters = [] } = useQuery({
    queryKey: ["chapters", projectId],
    queryFn: () => getChapters(projectId!),
    enabled: !!projectId,
  });

  const { data: versions = [] } = useQuery({
    queryKey: ["versions", projectId, chapterId],
    queryFn: () => getChapterVersions(projectId!, chapterId!),
    enabled: !!projectId && !!chapterId && showVersionsModal,
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => updateChapter(projectId!, chapterId!, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] }); setSaved(true); setSaving(false); },
    onError: () => setSaving(false),
  });

  const genChapterMutation = useMutation({
    mutationFn: () => generateChapter(chapterId!),
    onSuccess: () => { showMsg("✅ 章节生成完毕!"); queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] }); setShowGenModal(false); },
    onError: (e: any) => showMsg("❌ 生成失败: " + (e?.response?.data?.detail || e.message)),
  });

  const continueMutation = useMutation({
    mutationFn: () => continueChapter(chapterId!, promptText || undefined),
    onSuccess: () => { showMsg("✅ 续写完成!"); queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] }); setShowContinueModal(false); setPromptText(""); },
    onError: (e: any) => showMsg("❌ 续写失败: " + (e?.response?.data?.detail || e.message)),
  });

  const reviseMutation = useMutation({
    mutationFn: () => reviseChapter(chapterId!, promptText || undefined),
    onSuccess: () => { showMsg("✅ 修改完成!"); queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] }); setShowReviseModal(false); setPromptText(""); },
    onError: (e: any) => showMsg("❌ 修改失败: " + (e?.response?.data?.detail || e.message)),
  });

  const consistencyMutation = useMutation({
    mutationFn: () => checkConsistency(chapterId!),
    onSuccess: () => showMsg("✅ 一致性检查完成!"),
    onError: (e: any) => showMsg("❌ 检查失败: " + (e?.response?.data?.detail || e.message)),
  });

  const setVersionMutation = useMutation({
    mutationFn: (versionId: string) => setCurrentVersion(projectId!, chapterId!, versionId),
    onSuccess: () => { showMsg("✅ 版本已切换"); queryClient.invalidateQueries({ queryKey: ["chapter", projectId, chapterId] }); setShowVersionsModal(false); },
    onError: (e: any) => showMsg("❌ 切换失败: " + (e?.response?.data?.detail || e.message)),
  });

  const handleSave = () => { setSaving(true); updateMutation.mutate({ title, status, synopsis, notes, pov, characters, locations, content, outline, actual_words: content.replace(/[\s\n]/g, "").length }); };

  useEffect(() => { if (!saved && content !== (chapter?.content || "") && projectId && chapterId) { const timer = setTimeout(() => handleSave(), 30000); return () => clearTimeout(timer); } }, [content, saved]);
  useEffect(() => { const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); handleSave(); } }; document.addEventListener("keydown", h); return () => document.removeEventListener("keydown", h); }, [content, title, status]);

  if (isLoading) return <div className="p-8 text-gray-400">加载章节...</div>;
  const wordCount = content.replace(/[\s\n]/g, "").length;

  return (
    <div className="flex h-screen bg-[var(--bg-primary)]">
      <div className="w-64 border-r border-[var(--border)] flex flex-col">
        <div className="p-4 border-b border-[var(--border)]">
          <Link to={"/projects/" + projectId} className="text-sm text-indigo-400 hover:text-indigo-300">← 返回项目</Link>
          <h2 className="font-medium text-white text-sm mt-2">章节导航</h2>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {chapters.map((ch) => (
            <Link key={ch.id} to={"/projects/" + projectId + "/chapters/" + ch.id + "/edit"}
              className={"block px-3 py-2 rounded-lg text-sm transition-colors " + (ch.id === chapterId ? "bg-indigo-900/30 text-indigo-300 border border-indigo-700/30" : "text-gray-400 hover:text-gray-300 hover:bg-gray-800/30")}>
              <div className="flex items-center gap-2"><span className="text-xs text-gray-500">#{ch.chapter_number}</span><span className="truncate">{ch.title}</span></div>
            </Link>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {statusMsg && <div className="px-6 py-2 bg-indigo-900/30 text-indigo-300 text-sm border-b border-indigo-700/30">{statusMsg}</div>}
        <header className="border-b border-[var(--border)] px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <input type="text" className="text-lg font-semibold bg-transparent border-none text-white w-80 outline-none" value={title} onChange={(e) => { setTitle(e.target.value); setSaved(false); }} placeholder="章节标题" />
            <select className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-2 py-1 text-sm text-white" value={status} onChange={(e) => { setStatus(e.target.value); setSaved(false); }}>
              <option value="planned">已规划</option>
              <option value="generating">生成中</option>
              <option value="generated">已生成</option>
              <option value="reviewing">审查中</option>
              <option value="approved">已完成</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">{wordCount} 字</span>
            <Button variant="secondary" onClick={() => setShowGenModal(true)} className="text-xs">🤖 生成</Button>
            <Button variant="secondary" onClick={() => setShowContinueModal(true)} className="text-xs">✏️ 续写</Button>
            <Button variant="secondary" onClick={() => setShowReviseModal(true)} className="text-xs">🔄 修改</Button>
            <Button variant="secondary" onClick={() => consistencyMutation.mutate()} disabled={consistencyMutation.isPending} className="text-xs">{consistencyMutation.isPending ? "检查中..." : "✅ 一致性"}</Button>
            <Button variant="secondary" onClick={() => setShowVersionsModal(true)} className="text-xs">📋 版本</Button>
            <div className="w-px h-6 bg-gray-700" />
            <button className={"px-4 py-1.5 rounded-lg font-medium transition-colors text-sm " + (saved ? "bg-gray-800 text-gray-500" : "bg-indigo-600 hover:bg-indigo-700 text-white")} onClick={handleSave} disabled={saving || saved}>{saving ? "保存中..." : saved ? "已保存" : "保存"}</button>
          </div>
        </header>
        <textarea className="flex-1 w-full bg-transparent text-white p-6 resize-none outline-none text-base leading-relaxed font-serif" value={content} onChange={(e) => { setContent(e.target.value); setSaved(false); }} placeholder="开始写作..." />
      </div>

      <div className="w-72 border-l border-[var(--border)] p-4 space-y-4 overflow-y-auto">
        <div><h3 className="font-medium text-white text-sm mb-1">大纲</h3>
          <textarea className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-xs" rows={3} value={outline} onChange={(e) => { setOutline(e.target.value); setSaved(false); }} placeholder="本章节大纲..." /></div>
        <div><h3 className="font-medium text-white text-sm mb-1">摘要</h3>
          <textarea className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-xs" rows={2} value={synopsis} onChange={(e) => { setSynopsis(e.target.value); setSaved(false); }} placeholder="主要内容..." /></div>
        <div><h3 className="font-medium text-white text-sm mb-1">备注</h3>
          <textarea className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-xs" rows={2} value={notes} onChange={(e) => { setNotes(e.target.value); setSaved(false); }} placeholder="私人笔记..." /></div>
        <div><h3 className="font-medium text-white text-sm mb-1">POV</h3>
          <input type="text" className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-xs" value={pov} onChange={(e) => { setPov(e.target.value); setSaved(false); }} placeholder="视角" /></div>
        <div><h3 className="font-medium text-white text-sm mb-1">出场角色</h3>
          <input type="text" className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-xs" value={characters} onChange={(e) => { setCharacters(e.target.value); setSaved(false); }} placeholder="张三, 李四" /></div>
        <div><h3 className="font-medium text-white text-sm mb-1">地点</h3>
          <input type="text" className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-xs" value={locations} onChange={(e) => { setLocations(e.target.value); setSaved(false); }} placeholder="森林, 城堡" /></div>
      </div>

      <Modal open={showGenModal} onClose={() => setShowGenModal(false)} title="🤖 AI 生成章节">
        <div className="space-y-4"><p className="text-gray-400 text-sm">使用已配置的大模型生成本章内容。</p>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowGenModal(false)}>取消</Button>
            <Button onClick={() => genChapterMutation.mutate()} disabled={genChapterMutation.isPending}>{genChapterMutation.isPending ? "AI 生成中..." : "确认生成"}</Button>
          </div>
        </div>
      </Modal>

      <Modal open={showContinueModal} onClose={() => setShowContinueModal(false)} title="✏️ AI 续写">
        <div className="space-y-4"><p className="text-gray-400 text-sm">在当前位置继续往下写。</p>
          <div><label className="block text-sm font-medium text-gray-300 mb-1">续写方向（可选）</label>
            <textarea className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm" rows={3} value={promptText} onChange={(e) => setPromptText(e.target.value)} placeholder="例如：主角发现了一个惊天秘密..." /></div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowContinueModal(false)}>取消</Button>
            <Button onClick={() => continueMutation.mutate()} disabled={continueMutation.isPending}>{continueMutation.isPending ? "AI 续写中..." : "确认续写"}</Button>
          </div>
        </div>
      </Modal>

      <Modal open={showReviseModal} onClose={() => setShowReviseModal(false)} title="🔄 AI 修改">
        <div className="space-y-4"><p className="text-gray-400 text-sm">让 AI 根据修改意见重写本章节。</p>
          <div><label className="block text-sm font-medium text-gray-300 mb-1">修改意见</label>
            <textarea className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg px-3 py-2 text-white text-sm" rows={3} value={promptText} onChange={(e) => setPromptText(e.target.value)} placeholder="例如：让对话更自然，增加环境描写..." /></div>
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowReviseModal(false)}>取消</Button>
            <Button onClick={() => reviseMutation.mutate()} disabled={reviseMutation.isPending}>{reviseMutation.isPending ? "AI 修改中..." : "确认修改"}</Button>
          </div>
        </div>
      </Modal>

      <Modal open={showVersionsModal} onClose={() => setShowVersionsModal(false)} title="📋 版本历史">
        <div className="space-y-3">
          {versions.length === 0 ? <p className="text-gray-400 text-sm">暂无版本记录</p> : versions.map((v) => (
            <div key={v.id} className="bg-[var(--bg-card)] border border-[var(--border)] rounded-lg p-3 flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-white">v{v.version_number}</span>
                <span className="text-xs text-gray-400 ml-2">{v.word_count} 字 · {v.source}</span>
                <span className="text-xs text-gray-500 ml-2">{v.created_at ? new Date(v.created_at).toLocaleString("zh-CN") : ""}</span>
              </div>
              {chapter?.current_version_id !== v.id ? (
                <Button variant="secondary" className="text-xs" onClick={() => setVersionMutation.mutate(v.id)} disabled={setVersionMutation.isPending}>切换到此版本</Button>
              ) : <span className="text-xs text-green-400">当前版本</span>}
            </div>
          ))}
        </div>
      </Modal>
    </div>
  );
}