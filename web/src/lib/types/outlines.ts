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

export interface OutlinesData {
  topicTitle: string;
  summary: string;
  urgency: string;
  infoDensity: number;
  headlines: HeadlineSuggestion[];
  leadParagraph: string;
  outlineSections: OutlineSection[];
  interviewDirections: InterviewDirection[];
  references: ReferenceLink[];
}
