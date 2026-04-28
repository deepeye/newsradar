import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles } from "lucide-react";

interface AISummaryCardProps {
  summary: string;
  urgency: string;
  infoDensity: number;
}

export function AISummaryCard({ summary, urgency, infoDensity }: AISummaryCardProps) {
  return (
    <Card className="bg-card shadow-card border-0">
      <CardContent className="p-lg space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand" />
          <Badge variant="secondary" className="bg-brand/10 text-brand text-xs">
            AI 实时汇总
          </Badge>
          <div className="ml-auto flex items-center gap-2">
            <Badge className="bg-brand text-white text-xs">
              {urgency} (Breaking)
            </Badge>
            <Badge variant="outline" className="border-brand/30 text-brand text-xs">
              信息密度 {infoDensity}%
            </Badge>
          </div>
        </div>
        <p className="text-sm text-foreground/90 leading-relaxed">
          {summary}
        </p>
      </CardContent>
    </Card>
  );
}
