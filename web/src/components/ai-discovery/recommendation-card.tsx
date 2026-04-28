import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Newspaper, Flame } from "lucide-react";
import type { AITopicRecommendation } from "@/lib/types/ai-discovery";

const tagIcons: Record<string, typeof TrendingUp> = {
  newspaper: Newspaper,
  flame: Flame,
  "trending-up": TrendingUp,
};

interface RecommendationCardProps {
  recommendation: AITopicRecommendation;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const Icon = tagIcons[recommendation.sourceIcon] || TrendingUp;

  return (
    <Card className="bg-card shadow-card hover:shadow-card-hover transition-shadow border-0">
      <CardContent className="p-lg space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Badge
            variant="secondary"
            className="bg-brand/10 text-brand hover:bg-brand/15 text-xs font-medium"
          >
            <Icon className="h-3 w-3 mr-1" />
            {recommendation.tag}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {recommendation.source}
          </span>
        </div>

        {/* Title */}
        <h3 className="font-serif text-lg font-semibold text-foreground leading-snug">
          {recommendation.title}
        </h3>

        {/* AI Reason */}
        <div className="p-3 rounded-md bg-brand/5 border-l-2 border-brand">
          <p className="text-xs text-muted-foreground mb-1 font-medium">
            AI 推荐理由
          </p>
          <p className="text-sm text-foreground/90">{recommendation.reason}</p>
        </div>

        {/* Suggested angles */}
        <div>
          <p className="text-xs text-muted-foreground mb-2 font-medium">
            建议报道角度
          </p>
          <div className="space-y-2">
            {recommendation.angles.map((angle, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-sm text-foreground/80"
              >
                <span className="flex items-center justify-center h-5 w-5 rounded-full bg-muted text-xs text-muted-foreground shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span>{angle}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2">
          <Button className="bg-brand hover:bg-brand-dark text-white flex-1">
            生成大纲
          </Button>
          <Button variant="ghost" size="sm" className="text-muted-foreground">
            关闭
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
