import { Badge } from "@/components/ui/badge";
import type { ContentMetrics } from "@/lib/types/workbench";

interface AnalysisMetricsProps {
  metrics: ContentMetrics;
}

export function AnalysisMetrics({ metrics }: AnalysisMetricsProps) {
  return (
    <div className="flex items-center gap-4 p-3 bg-card rounded-md shadow-card">
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">客观性评分</span>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-16 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-tertiary rounded-full"
              style={{ width: `${metrics.objectivity}%` }}
            />
          </div>
          <span className="text-xs font-medium text-tertiary">{metrics.objectivity}%</span>
        </div>
      </div>
      <div className="w-px h-4 bg-outline-variant/30" />
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">阅读易读性</span>
        <Badge variant="outline" className="text-xs border-brand/30 text-brand">
          {metrics.readability}
        </Badge>
      </div>
    </div>
  );
}