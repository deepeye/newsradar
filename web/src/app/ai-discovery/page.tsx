"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAIDiscoveryData, useGenerateOutline, useRefreshDiscovery } from "@/lib/api/queries/ai-discovery";
import { OrgConfigCard } from "@/components/ai-discovery/org-config-card";
import { RecommendationCard } from "@/components/ai-discovery/recommendation-card";
import { SectionHeader } from "@/components/shared/section-header";
import { Button } from "@/components/ui/button";
import { Sparkles, ArrowRight, Clock, RefreshCw } from "lucide-react";
import type { AITopicRecommendation } from "@/lib/types/ai-discovery";

const LOADING_THRESHOLD = 2000;

export default function AIDiscoveryPage() {
  const { data, isLoading } = useAIDiscoveryData();
  const generateOutline = useGenerateOutline();
  const refreshDiscovery = useRefreshDiscovery();
  const router = useRouter();
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [showLoading, setShowLoading] = useState(false);

  // Only show loading UI after 2s threshold — fast cache hits skip it entirely
  useEffect(() => {
    if (!isLoading) {
      setShowLoading(false);
      return;
    }
    const timer = setTimeout(() => setShowLoading(true), LOADING_THRESHOLD);
    return () => clearTimeout(timer);
  }, [isLoading]);

  async function handleGenerateOutline(rec: AITopicRecommendation) {
    if (!data?.clueIds?.length) return;
    setGeneratingId(rec.id);
    try {
      const outline = await generateOutline.mutateAsync({
        clueIds: data.clueIds,
        additionalContext: `选题方向：${rec.title}。推荐理由：${rec.reason}。切入角度：${rec.angles.join("；")}`,
      });
      router.push(`/outlines?id=${outline.id}`);
    } catch {
      // error handled by mutation state
    } finally {
      setGeneratingId(null);
    }
  }

  if (isLoading && !data && showLoading) {
    return (
      <div className="max-w-[1400px] mx-auto px-lg py-lg space-y-lg">
        {/* Progress bar */}
        <div className="flex items-center justify-center py-[20vh]">
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-brand animate-pulse" />
              <span className="text-sm font-medium text-foreground">AI 正在分析线索，生成选题推荐...</span>
            </div>
            <div className="w-64 h-1.5 rounded-full bg-muted overflow-hidden">
              <div className="h-full rounded-full bg-brand animate-loading-bar" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-[1400px] mx-auto px-lg py-lg space-y-lg">
      {/* Org config */}
      <OrgConfigCard config={data.orgConfig} />

      {/* Section header */}
      <div className="flex items-center justify-between">
        <SectionHeader
          icon={Sparkles}
          title="AI 智能选题推荐"
          subtitle={`基于机构调性，AI 从 ${data.totalClues.toLocaleString()} 条线索中精选今日选题`}
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => refreshDiscovery.mutate()}
          disabled={refreshDiscovery.isPending}
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1 ${refreshDiscovery.isPending ? "animate-spin" : ""}`} />
          刷新推荐
        </Button>
      </div>

      {/* Last updated */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" />
        最后更新：{data.lastUpdated}
      </div>

      {/* Recommendation cards */}
      <div className="space-y-md">
        {data.recommendations.map((rec) => (
          <RecommendationCard
            key={rec.id}
            recommendation={rec}
            onGenerateOutline={handleGenerateOutline}
            isGenerating={generatingId === rec.id}
          />
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