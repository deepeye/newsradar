import type { TrendStatus, Platform } from "./index";

export interface TrendingItem {
  id: string;
  rank: number;
  title: string;
  heatValue: string;
  status?: TrendStatus;
  url?: string;
}

export interface PlatformTrendingCard {
  platform: Platform;
  platformLabel: string;
  items: TrendingItem[];
  lastUpdated: string;
}

export interface KOLPost {
  id: string;
  author: string;
  verified?: boolean;
  content: string;
  likes: number;
  shares: number;
  comments: number;
  timeAgo: string;
}

export interface KOLColumn {
  platform: string;
  platformLabel: string;
  posts: KOLPost[];
}

export interface AITopicSuggestion {
  id: string;
  title: string;
  description: string;
}

export interface DashboardData {
  trendingCards: PlatformTrendingCard[];
  kolColumns: KOLColumn[];
  aiSuggestions: AITopicSuggestion[];
  activeThreads: number;
  topicAlerts: number;
  quote: {
    text: string;
    source: string;
  };
}
