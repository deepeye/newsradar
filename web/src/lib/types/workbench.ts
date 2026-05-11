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
  leadParagraph: string | null;
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

export interface ContinueWritingResponse {
  continuedContent: string;
  sectionTitle: string;
}

export interface TranslateResponse {
  translatedContent: string;
  targetLanguage: string;
}

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "英文" },
  { code: "zh-TW", label: "中文繁体" },
  { code: "ru", label: "俄语" },
  { code: "ja", label: "日语" },
  { code: "ko", label: "韩语" },
  { code: "es", label: "西班牙语" },
  { code: "de", label: "德语" },
] as const;

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number]["code"];

export interface FactClaim {
  claim: string;
  type: string;
  confidence: string;
  searchQuery: string;
}

export interface SearchEvidence {
  title: string;
  snippet: string;
  source: string;
  url: string;
}

export interface FactCheckResult {
  claim: string;
  type: string;
  confidence: string;
  status: string;
  evidence: string;
  sourceUrls: string[];
}

export interface FactCheckResponse {
  claims: FactClaim[];
  searchResults: SearchEvidence[];
  results: FactCheckResult[];
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
