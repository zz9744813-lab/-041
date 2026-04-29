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
export const createProject = (data: { title: string; type?: string; description?: string }) => api.post<import('../types').Project>('/projects', data).then(r => r.data);
export const updateProject = (id: string, data: Partial<import('../types').Project>) => api.put<import('../types').Project>(`/projects/${id}`, data).then(r => r.data);
export const deleteProject = (id: string) => api.delete(`/projects/${id}`).then(r => r.data);

// ========== Chapters ==========
export const getChapters = (projectId: string) => api.get<import('../types').Chapter[]>(`/projects/${projectId}/chapters`).then(r => r.data);
export const getChapter = (projectId: string, chapterId: string) => api.get<import('../types').Chapter>(`/projects/${projectId}/chapters/${chapterId}`).then(r => r.data);
export const createChapter = (projectId: string, data: { title: string }) => api.post<import('../types').Chapter>(`/projects/${projectId}/chapters`, data).then(r => r.data);
export const updateChapter = (projectId: string, chapterId: string, data: Partial<import('../types').Chapter>) => api.put<import('../types').Chapter>(`/projects/${projectId}/chapters/${chapterId}`, data).then(r => r.data);
export const deleteChapter = (projectId: string, chapterId: string) => api.delete(`/projects/${projectId}/chapters/${chapterId}`).then(r => r.data);

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

export default api;