export interface HeadlineSuggestion {
  id: string;
  style: string;
  text: string;
}

export interface OutlineItem {
  id: string;
  content: string;
  hasAIRewrite: boolean;
}

export interface OutlineSection {
  id: string;
  number: string;
  title: string;
  items: OutlineItem[];
}

export interface InterviewDirection {
  id: string;
  role: string;
  description: string;
}

export interface ReferenceLink {
  id: string;
  title: string;
  source: string;
  url: string;
}

export interface OutlineResponse {
  id: string;
  title: string;
  summary: string | null;
  urgency: string;
  infoDensity: number;
  headlines: HeadlineSuggestion[] | null;
  leadParagraph: string | null;
  outlineSections: OutlineSection[] | null;
  interviewDirections: InterviewDirection[] | null;
  references: ReferenceLink[] | null;
  sourceClueIds: string[] | null;
  aiModel: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface OutlineListResponse {
  total: number;
  items: OutlineResponse[];
}
