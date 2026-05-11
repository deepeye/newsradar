import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingItem } from "./trending-item";
import type { PlatformTrendingCard as PlatformTrendingCardType } from "@/lib/types/dashboard";
import { MoreHorizontal } from "lucide-react";

const platformIcons: Record<string, string> = {
  weibo: "微博",
  douyin: "抖音",
  zhihu: "知乎",
  baidu: "百度",
  bilibili: "B站",
  toutiao: "头条",
  pengpai: "澎湃",
};

interface TrendingCardProps {
  card: PlatformTrendingCardType;
}

export function TrendingCard({ card }: TrendingCardProps) {
  return (
    <Card className="bg-card shadow-card hover:shadow-card-hover transition-shadow border-0">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-foreground">
            {platformIcons[card.platform] || card.platformLabel}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {card.lastUpdated}
            </span>
            <button className="p-1 rounded hover:bg-accent text-muted-foreground">
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="divide-y divide-outline-variant/20">
          {card.items.map((item) => (
            <TrendingItem key={item.id} item={item} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
