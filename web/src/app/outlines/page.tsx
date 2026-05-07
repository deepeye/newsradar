"use client";

import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useOutlinesList, useOutline } from "@/lib/api/queries/outlines";
import { BreadcrumbNav } from "@/components/outlines/breadcrumb-nav";
import { AISummaryCard } from "@/components/outlines/ai-summary-card";
import { HeadlineSuggestions } from "@/components/outlines/headline-suggestions";
import { LeadParagraph } from "@/components/outlines/lead-paragraph";
import { OutlineSectionList } from "@/components/outlines/outline-section";
import { InterviewDirections } from "@/components/outlines/interview-directions";
import { ReferenceLinks } from "@/components/outlines/reference-links";
import { Button } from "@/components/ui/button";
import { Share2, PenLine, FileText } from "lucide-react";

function OutlinesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const outlineId = searchParams.get("id");

  const { data: singleOutline, isLoading: loadingSingle } = useOutline(outlineId);
  const { data: outlineList, isLoading: loadingList } = useOutlinesList();

  const data = outlineId ? singleOutline : (outlineList?.items?.[0] ?? null);
  const isLoading = outlineId ? loadingSingle : loadingList;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!data || !data.title) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <FileText className="h-12 w-12 text-muted-foreground/40" />
        <h2 className="text-lg font-medium text-muted-foreground">暂无提纲</h2>
        <p className="text-sm text-muted-foreground">请先在 AI Discovery 中生成选题提纲</p>
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
          { label: data.title },
        ]}
      />

      {/* Title + actions */}
      <div className="flex items-start justify-between gap-4">
        <h1 className="font-serif text-2xl font-bold text-foreground leading-snug">
          {data.title}
        </h1>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" className="text-xs border-outline-variant/40">
            <Share2 className="h-3.5 w-3.5 mr-1" />
            分享协作
          </Button>
          <Button
            size="sm"
            className="text-xs bg-brand hover:bg-brand-dark text-white"
            onClick={() => router.push(`/workbench?outlineId=${data.id}`)}
          >
            <PenLine className="h-3.5 w-3.5 mr-1" />
            进入AI撰写模式
          </Button>
        </div>
      </div>

      {/* AI Summary */}
      <AISummaryCard
        summary={data.summary ?? ""}
        urgency={data.urgency}
        infoDensity={data.infoDensity}
      />

      {/* Headline suggestions */}
      {data.headlines && <HeadlineSuggestions headlines={data.headlines} />}

      {/* Lead paragraph */}
      {data.leadParagraph && <LeadParagraph paragraph={data.leadParagraph} />}

      {/* Structured outline */}
      {data.outlineSections && <OutlineSectionList sections={data.outlineSections} />}

      {/* Interview directions */}
      {data.interviewDirections && <InterviewDirections directions={data.interviewDirections} />}

      {/* Reference links */}
      {data.references && <ReferenceLinks references={data.references} />}
    </div>
  );
}

export default function OutlinesPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-[60vh]"><div className="text-muted-foreground">Loading...</div></div>}>
      <OutlinesContent />
    </Suspense>
  );
}
