"use client";

import { useWorkbenchData } from "@/lib/api/queries/workbench";
import { EditorStatusBar } from "@/components/workbench/editor-status-bar";
import { EditorToolbar } from "@/components/workbench/editor-toolbar";
import { EditorColumn } from "@/components/workbench/editor-column";
import { CopilotSidebar } from "@/components/workbench/copilot-sidebar";
import { AnalysisMetrics } from "@/components/workbench/analysis-metrics";
import { ToolButtons } from "@/components/workbench/tool-buttons";

export default function WorkbenchPage() {
  const { data, isLoading } = useWorkbenchData();

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col">
      {/* Top bar */}
      <div className="px-lg py-3 flex items-center justify-between">
        <EditorStatusBar
          wordCount={data.wordCount}
          targetWordCount={data.targetWordCount}
          completionPercent={data.completionPercent}
          lastSaved={data.lastSaved}
        />
        <ToolButtons />
      </div>

      {/* Main content - three column layout */}
      <div className="flex-1 px-lg pb-lg flex gap-md overflow-hidden">
        {/* Left nav sidebar */}
        <div className="w-[64px] shrink-0 bg-card rounded-md shadow-card flex flex-col items-center py-4 gap-3">
          <div className="h-8 w-8 rounded-md bg-brand/10 flex items-center justify-center text-brand">
            <span className="text-xs font-bold">1</span>
          </div>
          <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center text-muted-foreground">
            <span className="text-xs">2</span>
          </div>
          <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center text-muted-foreground">
            <span className="text-xs">3</span>
          </div>
          <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center text-muted-foreground">
            <span className="text-xs">4</span>
          </div>
        </div>

        {/* Editor column */}
        <div className="flex-1 min-w-0 flex flex-col gap-2 overflow-hidden">
          <EditorToolbar />
          <EditorColumn
            title={data.articleTitle}
            author={data.author}
            date={data.date}
            urgent={data.urgent}
            content={data.content}
          />
        </div>

        {/* Copilot sidebar */}
        <CopilotSidebar
          suggestions={data.suggestions}
          references={data.references}
        />
      </div>

      {/* Bottom metrics */}
      <div className="px-lg py-3">
        <AnalysisMetrics metrics={data.metrics} />
      </div>
    </div>
  );
}