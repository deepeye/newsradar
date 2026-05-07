"use client";

import { Suspense, useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useOutline } from "@/lib/api/queries/outlines";
import {
  useArticle,
  useCreateArticle,
  useSaveArticle,
  useAISuggest,
  useAIMetrics,
} from "@/lib/api/queries/workbench";
import { EditorStatusBar } from "@/components/workbench/editor-status-bar";
import { EditorToolbar } from "@/components/workbench/editor-toolbar";
import { EditorColumn } from "@/components/workbench/editor-column";
import { CopilotSidebar } from "@/components/workbench/copilot-sidebar";
import { AnalysisMetrics } from "@/components/workbench/analysis-metrics";
import { ToolButtons } from "@/components/workbench/tool-buttons";
import { PenLine } from "lucide-react";
import type { AISuggestion } from "@/lib/types/workbench";

function WorkbenchContent() {
  const searchParams = useSearchParams();
  const outlineId = searchParams.get("outlineId");
  const { data: outline, isLoading: outlineLoading } = useOutline(outlineId);

  const [articleId, setArticleId] = useState<string | null>(null);
  const [draftContent, setDraftContent] = useState<string>("");
  const [localSuggestions, setLocalSuggestions] = useState<AISuggestion[]>([]);
  const [useLocalSuggestions, setUseLocalSuggestions] = useState(false);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const createArticle = useCreateArticle();
  const saveArticle = useSaveArticle();
  const aiSuggest = useAISuggest();
  const aiMetrics = useAIMetrics();
  const { data: article, isLoading: articleLoading } = useArticle(articleId);

  // Create article from outline on first load
  useEffect(() => {
    if (!outline || articleId) return;
    const initContent = outline.leadParagraph
      ? `# ${outline.title}\n\n${outline.leadParagraph}`
      : `# ${outline.title}\n\n${outline.summary ?? ""}`;

    createArticle.mutate(
      {
        title: outline.title,
        outlineId: outline.id,
        targetWordCount: 3000,
        urgent: outline.urgency === "高",
      },
      {
        onSuccess: (created) => {
          setArticleId(created.id);
          setDraftContent(initContent);
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaust-deps
  }, [outline, articleId]);

  // Sync draft content when article loads
  useEffect(() => {
    if (article && draftContent === "" && article.content) {
      setDraftContent(article.content);
    }
  }, [article, draftContent]);

  // Debounced auto-save
  const triggerSave = useCallback(
    (content: string) => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        if (articleId) {
          saveArticle.mutate({ articleId, content });
        }
      }, 3000);
    },
    [articleId, saveArticle]
  );

  const handleContentChange = useCallback(
    (content: string) => {
      setDraftContent(content);
      triggerSave(content);
    },
    [triggerSave]
  );

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, []);

  // AI suggest handler
  const handleRequestSuggestions = useCallback(() => {
    if (!articleId) return;
    // Save content first before requesting suggestions
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveArticle.mutate(
      { articleId, content: draftContent },
      {
        onSuccess: () => {
          aiSuggest.mutate(articleId, {
            onSuccess: (result) => {
              if (result.aiSuggestions) {
                setLocalSuggestions(result.aiSuggestions);
                setUseLocalSuggestions(true);
              }
            },
          });
        },
      }
    );
  }, [articleId, draftContent, saveArticle, aiSuggest]);

  // Accept suggestion: replace original with suggested in content
  const handleAcceptSuggestion = useCallback(
    (suggestion: AISuggestion) => {
      if (draftContent.includes(suggestion.original)) {
        const newContent = draftContent.replace(
          suggestion.original,
          suggestion.suggested
        );
        setDraftContent(newContent);
        triggerSave(newContent);
      }
      setLocalSuggestions((prev) =>
        prev.filter((s) => s.id !== suggestion.id)
      );
    },
    [draftContent, triggerSave]
  );

  // Reject suggestion: remove from list
  const handleRejectSuggestion = useCallback((suggestionId: string) => {
    setLocalSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
  }, []);

  // Clear all suggestions
  const handleClearSuggestions = useCallback(() => {
    setLocalSuggestions([]);
    setUseLocalSuggestions(false);
  }, []);

  // AI metrics handler
  const handleAnalyzeMetrics = useCallback(() => {
    if (!articleId) return;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveArticle.mutate(
      { articleId, content: draftContent },
      {
        onSuccess: () => {
          aiMetrics.mutate(articleId);
        },
      }
    );
  }, [articleId, draftContent, saveArticle, aiMetrics]);

  // Loading states
  if (outlineLoading || (!articleId && createArticle.isPending)) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">
          {createArticle.isPending ? "正在创建文章..." : "Loading..."}
        </div>
      </div>
    );
  }

  if (!outlineId) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">请先选择选题</div>
      </div>
    );
  }

  if (!outline && !articleId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <PenLine className="h-12 w-12 text-muted-foreground/40" />
        <h2 className="text-lg font-medium text-muted-foreground">暂无文章</h2>
        <p className="text-sm text-muted-foreground">
          请先在 AI Discovery 中选择选题并生成提纲
        </p>
      </div>
    );
  }

  // Derived data
  const title = article?.title ?? outline?.title ?? "";
  const wordCount = draftContent.length;
  const targetWordCount = article?.targetWordCount ?? 3000;
  const completionPercent = Math.min(
    Math.round((wordCount / targetWordCount) * 100),
    100
  );
  const lastSaved = article?.lastSavedAt
    ? new Date(article.lastSavedAt).toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";
  const metrics = article?.metrics ?? {
    objectivity: outline?.infoDensity ?? 0,
    readability: "B2",
  };
  const references =
    article?.references ??
    (outline?.references ?? []).map((r) => ({
      id: r.id ?? "",
      title: r.title,
      source: r.source,
      lastUpdated: "",
    }));
  const sections = outline?.outlineSections ?? [];

  // Use local suggestions if user has interacted, otherwise article suggestions
  const suggestions = useLocalSuggestions
    ? localSuggestions
    : article?.aiSuggestions ?? [];

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col">
      {/* Top bar */}
      <div className="px-lg py-3 flex items-center justify-between">
        <EditorStatusBar
          wordCount={wordCount}
          targetWordCount={targetWordCount}
          completionPercent={completionPercent}
          lastSaved={lastSaved}
        />
        <ToolButtons
          onAnalyzeMetrics={handleAnalyzeMetrics}
          isAnalyzing={aiMetrics.isPending}
        />
      </div>

      {/* Main content - three column layout */}
      <div className="flex-1 px-lg pb-lg flex gap-md overflow-hidden">
        {/* Left nav sidebar */}
        <div className="w-[64px] shrink-0 bg-card rounded-md shadow-card flex flex-col items-center py-4 gap-3">
          {sections.map((section, i) => (
            <div
              key={section.id ?? i}
              className="h-8 w-8 rounded-md bg-brand/10 flex items-center justify-center text-brand"
            >
              <span className="text-xs font-bold">{section.number}</span>
            </div>
          ))}
        </div>

        {/* Editor column */}
        <div className="flex-1 min-w-0 flex flex-col gap-2 overflow-hidden">
          <EditorToolbar />
          <EditorColumn
            title={title}
            author={""}
            date={
              article?.createdAt
                ? new Date(article.createdAt).toLocaleDateString("zh-CN")
                : new Date().toLocaleDateString("zh-CN")
            }
            urgent={article?.urgent ?? false}
            content={draftContent}
            onContentChange={handleContentChange}
          />
        </div>

        {/* Copilot sidebar */}
        <CopilotSidebar
          suggestions={suggestions}
          references={references}
          onRequestSuggestions={handleRequestSuggestions}
          isRequestingSuggestions={aiSuggest.isPending}
          onAcceptSuggestion={handleAcceptSuggestion}
          onRejectSuggestion={handleRejectSuggestion}
          onClearSuggestions={handleClearSuggestions}
        />
      </div>

      {/* Bottom metrics */}
      <div className="px-lg py-3">
        <AnalysisMetrics metrics={metrics} />
      </div>
    </div>
  );
}

export default function WorkbenchPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      }
    >
      <WorkbenchContent />
    </Suspense>
  );
}
