"use client";

import { useDashboardData } from "@/lib/api/queries/dashboard";
import { TrendingGrid } from "@/components/dashboard/trending-grid";
import { KOLSection } from "@/components/dashboard/kol-section";
import { AIAssistantCard } from "@/components/dashboard/ai-assistant-card";
import { StatsBar } from "@/components/dashboard/stats-bar";
import { SectionHeader } from "@/components/shared/section-header";
import { TrendingUp, Flame } from "lucide-react";

export default function DashboardPage() {
  const { data, isLoading } = useDashboardData();

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-lg py-lg space-y-lg">
      {/* Page header */}
      <SectionHeader
        icon={TrendingUp}
        title="首页热榜聚合"
        subtitle="Real-time cross-platform newsroom pulse."
      />

      {/* Trending grid */}
      <TrendingGrid cards={data.trendingCards} />

      {/* KOL section */}
      <KOLSection columns={data.kolColumns} />

      {/* AI Assistant */}
      <AIAssistantCard suggestions={data.aiSuggestions} />

      {/* Stats bar */}
      <StatsBar
        activeThreads={data.activeThreads}
        topicAlerts={data.topicAlerts}
      />

      {/* Quote block */}
      <div className="flex items-start gap-3 py-4 px-lg bg-card rounded-md shadow-card">
        <Flame className="h-5 w-5 text-brand shrink-0 mt-0.5" />
        <div>
          <p className="font-serif text-base italic text-foreground/80">
            &ldquo;{data.quote.text}&rdquo;
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            — {data.quote.source}
          </p>
        </div>
      </div>
    </div>
  );
}
