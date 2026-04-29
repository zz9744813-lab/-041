export interface Project {
  id: string;
  title: string;
  type: string;
  description: string;
  status: 'active' | 'completed' | 'paused' | 'draft';
  word_count: number;
  chapter_count: number;
  created_at: string;
  updated_at: string;
}

export interface Chapter {
  id: string;
  project_id: string;
  title: string;
  content: string;
  status: 'draft' | 'writing' | 'revised' | 'completed';
  synopsis: string;
  notes: string;
  pov: string;
  characters: string;
  locations: string;
  word_count: number;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  role: string;
  age: string;
  gender: string;
  appearance: string;
  personality: string;
  background: string;
  motivation: string;
  arc: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface WorldItem {
  id: string;
  project_id: string;
  name: string;
  category: 'location' | 'timeline' | 'rule' | 'lore';
  content: string;
  created_at: string;
  updated_at: string;
}

export interface WritingSession {
  id: string;
  project_id: string;
  chapter_id: string;
  word_count: number;
  duration_minutes: number;
  date: string;
}

export interface DashboardStats {
  total_projects: number;
  total_words: number;
  total_chapters: number;
  daily_words: { date: string; words: number }[];
  project_progress: {
    id: string;
    title: string;
    word_count: number;
    chapter_count: number;
    status: string;
  }[];
}