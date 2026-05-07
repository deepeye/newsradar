export interface OrgConfig {
  domains: string[];
  style: string[];
}

export interface AITopicRecommendation {
  id: string;
  source: string;
  sourceIcon: string;
  tag: string;
  title: string;
  reason: string;
  angles: string[];
}

export interface AIDiscoveryData {
  orgConfig: OrgConfig;
  totalClues: number;
  lastUpdated: string;
  clueIds: string[];
  recommendations: AITopicRecommendation[];
  totalRecommendations: number;
}
