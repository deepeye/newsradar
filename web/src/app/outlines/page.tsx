"use client";

import { useOutlinesData } from "@/lib/api/queries/outlines";
import { BreadcrumbNav } from "@/components/outlines/breadcrumb-nav";
import { AISummaryCard } from "@/components/outlines/ai-summary-card";
import { HeadlineSuggestions } from "@/components/outlines/headline-suggestions";
import { LeadParagraph } from "@/components/outlines/lead-paragraph";
import { OutlineSectionList } from "@/components/outlines/outline-section";
import { InterviewDirections } from "@/components/outlines/interview-directions";
import { ReferenceLinks } from "@/components/outlines/reference-links";
import { Button } from "@/components/ui/button";
import { Share2, PenLine } from "lucide-react";

export default function OutlinesPage() {
  const { data, isLoading } = useOutlinesData();

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-lg py-lg space-y-lg">
      {/* Breadcrumb */}
      <BreadcrumbNav
        items={[
          { label: "NEWSROOM", href: "/" },
          { label: "AI OUTLINES", href: "/ai-discovery" },
          { label: "CURRENT GENERATION" },
        ]}
      />

      {/* Title + actions */}
      <div className="flex items-start justify-between gap-4">
        <h1 className="font-serif text-2xl font-bold text-foreground leading-snug">
          {data.topicTitle}
        </h1>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" className="text-xs border-outline-variant/40">
            <Share2 className="h-3.5 w-3.5 mr-1" />
            分享协作
          </Button>
          <Button size="sm" className="text-xs bg-brand hover:bg-brand-dark text-white">
            <PenLine className="h-3.5 w-3.5 mr-1" />
            进入AI撰写模式
          </Button>
        </div>
      </div>

      {/* AI Summary */}
      <AISummaryCard
        summary={data.summary}
        urgency={data.urgency}
        infoDensity={data.infoDensity}
      />

      {/* Headline suggestions */}
      <HeadlineSuggestions headlines={data.headlines} />

      {/* Lead paragraph */}
      <LeadParagraph paragraph={data.leadParagraph} />

      {/* Structured outline */}
      <OutlineSectionList sections={data.outlineSections} />

      {/* Interview directions */}
      <InterviewDirections directions={data.interviewDirections} />

      {/* Reference links */}
      <ReferenceLinks references={data.references} />
    </div>
  );
}
