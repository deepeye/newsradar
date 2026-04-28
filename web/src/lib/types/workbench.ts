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

export interface WorkbenchData {
  articleTitle: string;
  author: string;
  date: string;
  urgent: boolean;
  content: string;
  wordCount: number;
  targetWordCount: number;
  completionPercent: number;
  lastSaved: string;
  suggestions: AISuggestion[];
  metrics: ContentMetrics;
  references: ReferenceDoc[];
}
