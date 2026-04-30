import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ========== Stats ==========
export const getDashboardStats = () => api.get<import('../types').DashboardStats>('/stats/overview').then(r => r.data);

// ========== Projects ==========
export const getProjects = () => api.get<import('../types').Project[]>('/projects').then(r => r.data);
export const getProject = (id: string) => api.get<import('../types').Project>(`/projects/${id}`).then(r => r.data);
export const createProject = (data: import('../types').ProjectCreate) => api.post<import('../types').Project>('/projects', data).then(r => r.data);
export const updateProject = (id: string, data: Partial<import('../types').Project>) => api.put<import('../types').Project>(`/projects/${id}`, data).then(r => r.data);
export const deleteProject = (id: string) => api.delete(`/projects/${id}`).then(r => r.data);

// ========== Chapters ==========
export const getChapters = (projectId: string) => api.get<import('../types').Chapter[]>(`/projects/${projectId}/chapters`).then(r => r.data);
export const getChapter = (projectId: string, chapterId: string) => api.get<import('../types').ChapterDetail>(`/projects/${projectId}/chapters/${chapterId}`).then(r => r.data);
export const createChapter = (projectId: string, data: import('../types').ChapterCreate) => api.post<import('../types').ChapterDetail>(`/projects/${projectId}/chapters`, data).then(r => r.data);
export const updateChapter = (projectId: string, chapterId: string, data: Partial<import('../types').Chapter>) => api.put<import('../types').ChapterDetail>(`/projects/${projectId}/chapters/${chapterId}`, data).then(r => r.data);
export const deleteChapter = (projectId: string, chapterId: string) => api.delete(`/projects/${projectId}/chapters/${chapterId}`).then(r => r.data);
export const getChapterVersions = (projectId: string, chapterId: string) => api.get<import('../types').ChapterVersion[]>(`/projects/${projectId}/chapters/${chapterId}/versions`).then(r => r.data);
export const setCurrentVersion = (projectId: string, chapterId: string, versionId: string) => api.post(`/projects/${projectId}/chapters/${chapterId}/versions/${versionId}/set-current`).then(r => r.data);

// ========== Characters ==========
export const getCharacters = (projectId: string) => api.get<import('../types').Character[]>(`/projects/${projectId}/characters`).then(r => r.data);
export const createCharacter = (projectId: string, data: Partial<import('../types').Character>) => api.post<import('../types').Character>(`/projects/${projectId}/characters`, data).then(r => r.data);
export const updateCharacter = (projectId: string, characterId: string, data: Partial<import('../types').Character>) => api.put<import('../types').Character>(`/projects/${projectId}/characters/${characterId}`, data).then(r => r.data);
export const deleteCharacter = (projectId: string, characterId: string) => api.delete(`/projects/${projectId}/characters/${characterId}`).then(r => r.data);

// ========== World Items ==========
export const getWorldItems = (projectId: string) => api.get<import('../types').WorldItem[]>(`/projects/${projectId}/world`).then(r => r.data);
export const createWorldItem = (projectId: string, data: Partial<import('../types').WorldItem>) => api.post<import('../types').WorldItem>(`/projects/${projectId}/world`, data).then(r => r.data);
export const updateWorldItem = (projectId: string, worldId: string, data: Partial<import('../types').WorldItem>) => api.put<import('../types').WorldItem>(`/projects/${projectId}/world/${worldId}`, data).then(r => r.data);
export const deleteWorldItem = (projectId: string, worldId: string) => api.delete(`/projects/${projectId}/world/${worldId}`).then(r => r.data);

// ========== Model Configs (Settings) ==========
export const getModelConfigs = () => api.get<import('../types').ModelConfig[]>('/model-configs').then(r => r.data);
export const createModelConfig = (data: import('../types').ModelConfigCreate) => api.post<import('../types').ModelConfig>('/model-configs', data).then(r => r.data);
export const updateModelConfig = (id: string, data: Partial<import('../types').ModelConfig>) => api.put<import('../types').ModelConfig>(`/model-configs/${id}`, data).then(r => r.data);
export const deleteModelConfig = (id: string) => api.delete(`/model-configs/${id}`).then(r => r.data);
export const testModelConfig = (id: string) => api.post(`/model-configs/${id}/test`).then(r => r.data);

// ========== AI Generation ==========
export const generateSetting = (projectId: string) => api.post<import('../types').GenerationJob>(`/projects/${projectId}/generate-setting`).then(r => r.data);
export const generateOutline = (projectId: string) => api.post<import('../types').GenerationJob>(`/projects/${projectId}/generate-outline`).then(r => r.data);
export const generateAll = (projectId: string) => api.post<import('../types').GenerationJob[]>(`/projects/${projectId}/generate-all`).then(r => r.data);
export const generateChapter = (chapterId: string) => api.post<import('../types').GenerationJob>(`/chapters/${chapterId}/generate`).then(r => r.data);
export const continueChapter = (chapterId: string, prompt?: string) => api.post<import('../types').GenerationJob>(`/chapters/${chapterId}/continue`, { continuation_prompt: prompt }).then(r => r.data);
export const reviseChapter = (chapterId: string, instructions?: string) => api.post<import('../types').GenerationJob>(`/chapters/${chapterId}/revise`, { revision_instructions: instructions }).then(r => r.data);
export const checkConsistency = (chapterId: string) => api.post<import('../types').GenerationJob>(`/chapters/${chapterId}/check-consistency`).then(r => r.data);

// ========== Jobs ==========
export const getJobs = (projectId?: string) => {
  const params = projectId ? { params: { project_id: projectId } } : {};
  return api.get<import('../types').GenerationJob[]>('/jobs', params).then(r => r.data);
};
export const getJob = (jobId: string) => api.get<import('../types').GenerationJob>(`/jobs/${jobId}`).then(r => r.data);
export const retryJob = (jobId: string) => api.post(`/jobs/${jobId}/retry`).then(r => r.data);
export const cancelJob = (jobId: string) => api.post(`/jobs/${jobId}/cancel`).then(r => r.data);

// ========== Autogen ==========
export const startAutogen = (projectId: string, options?: import('../types').AutogenOptions) => api.post<import('../types').AutogenStatus>(`/projects/${projectId}/autogen/start`, options || {}).then(r => r.data);
export const pauseAutogen = (projectId: string) => api.post<import('../types').AutogenStatus>(`/projects/${projectId}/autogen/pause`).then(r => r.data);
export const resumeAutogen = (projectId: string) => api.post<import('../types').AutogenStatus>(`/projects/${projectId}/autogen/resume`).then(r => r.data);
export const stopAutogen = (projectId: string) => api.post<import('../types').AutogenStatus>(`/projects/${projectId}/autogen/stop`).then(r => r.data);
export const getAutogenStatus = (projectId: string) => api.get<import('../types').AutogenStatus>(`/projects/${projectId}/autogen/status`).then(r => r.data);

// ========== CanonFacts ==========
export const getCanonFacts = (projectId: string) => api.get<import('../types').CanonFact[]>(`/projects/${projectId}/canon-facts`).then(r => r.data);
export const createCanonFact = (projectId: string, data: Partial<import('../types').CanonFact>) => api.post<import('../types').CanonFact>(`/projects/${projectId}/canon-facts`, data).then(r => r.data);

// ========== StoryArcs ==========
export const getStoryArcs = (projectId: string) => api.get<import('../types').StoryArc[]>(`/projects/${projectId}/story-arcs`).then(r => r.data);
export const createStoryArc = (projectId: string, data: Partial<import('../types').StoryArc>) => api.post<import('../types').StoryArc>(`/projects/${projectId}/story-arcs`, data).then(r => r.data);

// ========== Foreshadowings ==========
export const getForeshadowings = (projectId: string) => api.get<import('../types').Foreshadowing[]>(`/projects/${projectId}/foreshadowings`).then(r => r.data);
export const createForeshadowing = (projectId: string, data: Partial<import('../types').Foreshadowing>) => api.post<import('../types').Foreshadowing>(`/projects/${projectId}/foreshadowings`, data).then(r => r.data);

export default api;