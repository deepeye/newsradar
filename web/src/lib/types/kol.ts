export interface KOLProfile {
  id: string;
  sourceId: string;
  platform: "weibo" | "x";
  platformId: string;
  screenName: string;
  avatarUrl?: string;
  bio?: string;
  followerCount?: number;
  followingCount?: number;
  postCount?: number;
  isActive: boolean;
  lastSyncedAt?: string;
  cookieStatus?: { active: number; invalid: number; expired: number };
  createdAt: string;
  updatedAt: string;
}

export interface KOLPost {
  id: string;
  content: string;
  url?: string;
  author?: string;
  likes: number;
  comments: number;
  shares: number;
  coverImage?: string;
  collectedAt: string;
}

export interface KOLCreateRequest {
  platform: "weibo" | "x";
  platformId: string;
  screenName: string;
  avatarUrl?: string;
  bio?: string;
  cookies?: Record<string, string>;
}

export interface KOLCookieImportRequest {
  cookies: Record<string, string>;
}

export interface KOLListResponse {
  total: number;
  items: KOLProfile[];
}

export interface KOLPostListResponse {
  total: number;
  items: KOLPost[];
}
