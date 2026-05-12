"use client";

import { Suspense, useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useOutline } from "@/lib/api/queries/outlines";
import {
  useArticle,
  useCreateArticle,
  useSaveArticle,
  useAISuggest,
  useAIContinueWriting,
  useAITranslate,
  useAIFactCheck,
  useGenerateArticleFromOutlineStream,
} from "@/lib/api/queries/workbench";
import { EditorStatusBar } from "@/components/workbench/editor-status-bar";
import { EditorToolbar } from "@/components/workbench/editor-toolbar";
import { EditorColumn } from "@/components/workbench/editor-column";
import { CopilotSidebar } from "@/components/workbench/copilot-sidebar";
import { AnalysisMetrics } from "@/components/workbench/analysis-metrics";
import { ToolButtons } from "@/components/workbench/tool-buttons";
import { HeadlineSelector } from "@/components/workbench/headline-selector";
import { PenLine } from "lucide-react";
import type { AISuggestion, LanguageCode, FactCheckResult } from "@/lib/types/workbench";

function WorkbenchContent() {
  const searchParams = useSearchParams();
  const outlineId = searchParams.get("outlineId");
  const { data: outline, isLoading: outlineLoading } = useOutline(outlineId);

  const [articleId, setArticleId] = useState<string | null>(null);
  const [draftContent, setDraftContent] = useState<string>("");
  const [localSuggestions, setLocalSuggestions] = useState<AISuggestion[]>([]);
  const [useLocalSuggestions, setUseLocalSuggestions] = useState(false);
  const [factCheckResults, setFactCheckResults] = useState<FactCheckResult[]>([]);
  const [dateStr, setDateStr] = useState("");
  const [showHeadlineSelector, setShowHeadlineSelector] = useState(false);
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const createArticle = useCreateArticle();
  const generateStream = useGenerateArticleFromOutlineStream();
  const saveArticle = useSaveArticle();
  const aiSuggest = useAISuggest();
    const continueWriting = useAIContinueWriting();
  const aiTranslate = useAITranslate();
  const aiFactCheck = useAIFactCheck();
  const { data: article, isLoading: articleLoading } = useArticle(articleId);

  // Client-only date string to avoid hydration mismatch
  useEffect(() => {
    setDateStr(
      article?.createdAt
        ? new Date(article.createdAt).toLocaleDateString("zh-CN")
        : new Date().toLocaleDateString("zh-CN")
    );
  }, [article?.createdAt]);

  // Derived title — used by suggestion handler before rendering
  const title = article?.title ?? outline?.title ?? "";

  // Show headline selector when outline loads
  useEffect(() => {
    if (!outline || articleId) return;
    if (outline.headlines && outline.headlines.length > 0) {
      setShowHeadlineSelector(true);
    } else {
      // No headlines — generate directly with outline title
      generateStream.mutate(
        { outlineId: outline.id, headlineIndex: null },
        {
          onCreated: (data) => {
            setArticleId(data.articleId);
            setDraftContent(`# ${data.title}\n\n${data.leadParagraph ?? ""}\n\n`);
          },
          onChunk: (content) => {
            setDraftContent((prev) => prev + content);
          },
          onDone: () => {},
        }
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [outline, articleId]);

  // Handle headline selection
  const handleHeadlineSelect = useCallback(
    (headlineIndex: number | null, selectedTitle: string) => {
      setShowHeadlineSelector(false);
      if (!outline) return;
      generateStream.mutate(
        { outlineId: outline.id, headlineIndex },
        {
          onCreated: (data) => {
            setArticleId(data.articleId);
            setDraftContent(`# ${data.title}\n\n${data.leadParagraph ?? ""}\n\n`);
          },
          onChunk: (content) => {
            setDraftContent((prev) => prev + content);
          },
          onDone: () => {},
        }
      );
    },
    [outline, generateStream]
  );

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
    if (!draftContent) return;
    aiSuggest.mutate(
      { title, content: draftContent },
      {
        onSuccess: (result) => {
          if (result.aiSuggestions) {
            setLocalSuggestions(result.aiSuggestions);
            setUseLocalSuggestions(true);
          }
        },
      }
    );
  }, [draftContent, title, aiSuggest]);

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

  
  // Continue writing handler
  const handleContinueWriting = useCallback(() => {
    if (!articleId) return;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveArticle.mutate(
      { articleId, content: draftContent },
      {
        onSuccess: () => {
          continueWriting.mutate(articleId, {
            onSuccess: (result) => {
              if (result.continuedContent) {
                const separator = result.sectionTitle
                  ? `\n\n## ${result.sectionTitle}\n\n`
                  : "\n\n";
                const newContent = draftContent + separator + result.continuedContent;
                setDraftContent(newContent);
                triggerSave(newContent);
              }
            },
          });
        },
      }
    );
  }, [articleId, draftContent, saveArticle, continueWriting, triggerSave]);

  // Translate handler
  const handleTranslate = useCallback(
    (targetLanguage: LanguageCode) => {
      if (!articleId) return;
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveArticle.mutate(
        { articleId, content: draftContent },
        {
          onSuccess: () => {
            aiTranslate.mutate(
              { articleId, targetLanguage },
              {
                onSuccess: (result) => {
                  if (result.translatedContent) {
                    setDraftContent(result.translatedContent);
                    triggerSave(result.translatedContent);
                  }
                },
              }
            );
          },
        }
      );
    },
    [articleId, draftContent, saveArticle, aiTranslate, triggerSave]
  );

  // Fact-check handler
  const handleFactCheck = useCallback(() => {
    if (!articleId) return;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveArticle.mutate(
      { articleId, content: draftContent },
      {
        onSuccess: () => {
          aiFactCheck.mutate(articleId, {
            onSuccess: (result) => {
              if (result.results) {
                setFactCheckResults(result.results);
              }
            },
          });
        },
      }
    );
  }, [articleId, draftContent, saveArticle, aiFactCheck]);

  const handleClearFactCheck = useCallback(() => {
    setFactCheckResults([]);
  }, []);

  // Loading states
  if (outlineLoading || (!articleId && (showHeadlineSelector === false && generateStream.isPending))) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">
          {generateStream.isPending ? "正在生成初稿..." : "Loading..."}
        </div>
      </div>
    );
  }

  // Show headline selector modal
  if (showHeadlineSelector && outline) {
    return (
      <HeadlineSelector
        headlines={outline.headlines ?? []}
        defaultTitle={outline.title}
        onSelect={handleHeadlineSelect}
        isGenerating={generateStream.isPending}
      />
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
    (outline?.references ?? []).map((r, i) => ({
      id: r.id ?? `ref-${i}`,
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
          onTranslate={handleTranslate}
          isTranslating={aiTranslate.isPending}
          onFactCheck={handleFactCheck}
          isFactChecking={aiFactCheck.isPending}
        />
      </div>

      {/* Main content - three column layout */}
      <div className="flex-1 px-lg pb-lg flex gap-md overflow-hidden">
        {/* Left nav sidebar */}
        <div className="w-[64px] shrink-0 bg-card rounded-md shadow-card flex flex-col items-center py-4 gap-2">
          {sections.map((section, i) => (
            <div
              key={section.id ?? i}
              title={section.title}
              className="h-8 w-8 rounded-md bg-brand/8 hover:bg-brand/15 transition-colors flex items-center justify-center text-brand cursor-default"
            >
              <span className="text-xs font-bold">{section.number}</span>
            </div>
          ))}
        </div>

        {/* Editor column */}
        <div className="flex-1 min-w-0 flex flex-col gap-2 overflow-hidden">
          <EditorToolbar
            onContinueWriting={handleContinueWriting}
            isContinuingWriting={continueWriting.isPending}
          />
          <EditorColumn
            title={title}
            author={""}
            date={dateStr}
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
          factCheckResults={factCheckResults}
          onClearFactCheck={handleClearFactCheck}
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
