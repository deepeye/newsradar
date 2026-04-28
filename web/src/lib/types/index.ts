// Shared types for the NewsRadar frontend

export type TrendStatus = "explosive" | "new" | "rank_up" | "rank_down" | "stable";

export type Platform = "weibo" | "douyin" | "zhihu" | "baidu" | "bilibili" | "toutiao" | "twitter";

export type CategoryFilter = "all" | "society" | "tech" | "finance";

export interface NavItem {
  label: string;
  href: string;
  icon: string; // lucide icon name
}
