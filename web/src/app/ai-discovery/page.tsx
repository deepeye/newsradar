"use client";

import { useAIDiscoveryData } from "@/lib/api/queries/ai-discovery";
import { OrgConfigCard } from "@/components/ai-discovery/org-config-card";
import { RecommendationCard } from "@/components/ai-discovery/recommendation-card";
import { SectionHeader } from "@/components/shared/section-header";
import { Button } from "@/components/ui/button";
import { Sparkles, ArrowRight, Clock } from "lucide-react";

export default function AIDiscoveryPage() {
  const { data, isLoading } = useAIDiscoveryData();

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-lg py-lg space-y-lg">
      {/* Org config */}
      <OrgConfigCard config={data.orgConfig} />

      {/* Section header */}
      <SectionHeader
        icon={Sparkles}
        title="AI 智能选题推荐"
        subtitle={`基于机构调性，AI 从 ${data.totalClues.toLocaleString()} 条线索中精选今日选题`}
      />

      {/* Last updated */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" />
        最后更新：{data.lastUpdated}
      </div>

      {/* Recommendation cards */}
      <div className="space-y-md">
        {data.recommendations.map((rec) => (
          <RecommendationCard key={rec.id} recommendation={rec} />
        ))}
      </div>

      {/* Bottom CTA */}
      <div className="flex items-center justify-between p-md bg-gradient-to-r from-brand/5 to-tertiary/5 rounded-md border border-brand/10">
        <div>
          <p className="font-medium text-foreground">想要更多个性化推荐？</p>
          <p className="text-sm text-muted-foreground">
            可调整机构调性配置，让AI学习细分报道喜好与历史采纳偏好
          </p>
        </div>
        <Button className="bg-brand hover:bg-brand-dark text-white shrink-0">
          立即优化算法
          <ArrowRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
        <span>
          展示 1-{data.recommendations.length} 条，共 {data.totalRecommendations} 条推荐
        </span>
        <div className="flex items-center gap-1 ml-4">
          <Button variant="outline" size="sm" disabled className="h-7 w-7 p-0">
            &lt;
          </Button>
          <Button variant="outline" size="sm" className="h-7 w-7 p-0 bg-brand text-white border-brand">
            1
          </Button>
          <Button variant="outline" size="sm" className="h-7 w-7 p-0">
            2
          </Button>
          <Button variant="outline" size="sm" className="h-7 w-7 p-0">
            3
          </Button>
          <Button variant="outline" size="sm" className="h-7 w-7 p-0">
            &gt;
          </Button>
        </div>
      </div>
    </div>
  );
}
