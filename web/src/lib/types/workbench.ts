export interface AISuggestion {
  id: string;
  type: "grammar" | "style" | "fact";
  original: string;
  suggested: string;
  reason: string;
}

export interface ContentMetrics {
  objectivity: number;
  readability: string;
}

export interface ReferenceDoc {
  id: string;
  title: string;
  source: string;
  lastUpdated: string;
}

export interface ArticleResponse {
  id: string;
  outlineId: string | null;
  title: string;
  authorId: string | null;
  content: string | null;
  wordCount: number;
  targetWordCount: number;
  completionPercent: number;
  urgent: boolean;
  aiSuggestions: AISuggestion[] | null;
  metrics: ContentMetrics | null;
  references: ReferenceDoc[] | null;
  status: string;
  lastSavedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ArticleCreateRequest {
  title: string;
  outlineId?: string;
  targetWordCount?: number;
  urgent?: boolean;
}

export interface ArticleSaveRequest {
  content?: string;
  title?: string;
}
