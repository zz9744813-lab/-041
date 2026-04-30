export interface Project {
  id: string;
  title: string;
  description: string;
  idea: string;
  genre: string;
  style: string;
  target_words: number;
  type: string;
  status: 'idea' | 'setting_generated' | 'outline_generated' | 'generating' | 'paused' | 'completed' | 'failed';
  word_count: number;
  chapter_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  title: string;
  description?: string;
  idea?: string;
  genre?: string;
  style?: string;
  target_words?: number;
  type?: string;
}

export interface Chapter {
  id: string;
  project_id: string;
  volume_id: string | null;
  title: string;
  chapter_number: number;
  status: 'planned' | 'generating' | 'generated' | 'reviewing' | 'approved' | 'failed';
  word_count: number;
  outline: string;
  summary: string;
  current_version_id: string | null;
  target_words: number;
  actual_words: number;
  synopsis: string | null;
  notes: string | null;
  pov: string | null;
  characters: string | null;
  locations: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChapterDetail extends Chapter {
  content: string;
}

export interface ChapterCreate {
  title: string;
  status?: string;
  outline?: string;
  target_words?: number;
  synopsis?: string;
  notes?: string;
  pov?: string;
  characters?: string;
  locations?: string;
  content?: string;
}

export interface ChapterVersion {
  id: string;
  chapter_id: string;
  version_number: number;
  content: string;
  word_count: number;
  source: string;
  created_at: string;
}

export interface Character {
  id: string;
  project_id: string;
  name: string;
  age: string | null;
  gender: string | null;
  personality: string | null;
  background: string | null;
  appearance: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelConfig {
  id: string;
  name: string;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
  max_tokens: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModelConfigCreate {
  name: string;
  base_url: string;
  api_key: string;
  model: string;
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
}

export interface WorldItem {
  id: string;
  project_id: string;
  title: string;
  category: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface GenerationJob {
  id: string;
  project_id: string | null;
  chapter_id: string | null;
  job_type: string;
  status: string;
  progress: number;
  input_snapshot: string;
  output_text: string;
  error_message: string;
  retry_count: number;
  max_retries: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface AutogenStatus {
  project_id: string;
  running: boolean;
  current_chapter: number | null;
  current_chapter_id: string | null;
  total_chapters: number;
  completed_chapters: number;
  failed_chapters: number;
  progress: number;
  status: string;
  error_message: string;
  started_at: string | null;
}

export interface AutogenOptions {
  start_chapter?: number;
  end_chapter?: number;
  max_chapters?: number;
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

export interface CanonFact {
  id: string;
  project_id: string;
  fact: string;
  category: string;
  source: string;
  created_at: string;
}

export interface StoryArc {
  id: string;
  project_id: string;
  title: string;
  description: string;
  start_chapter: number;
  end_chapter: number;
  created_at: string;
}

export interface Foreshadowing {
  id: string;
  project_id: string;
  hint: string;
  target_chapter: number;
  category: string;
  resolved: boolean;
  created_at: string;
}

export interface CanonFact {
  id: string;
  project_id: string;
  fact: string;
  category: string;
  source: string;
  created_at: string;
}

export interface StoryArc {
  id: string;
  project_id: string;
  title: string;
  description: string;
  start_chapter: number;
  end_chapter: number;
  created_at: string;
}

export interface Foreshadowing {
  id: string;
  project_id: string;
  hint: string;
  target_chapter: number;
  category: string;
  resolved: boolean;
  created_at: string;
}
