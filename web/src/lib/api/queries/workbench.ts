"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchFromApi, fetchFromApiSSE } from "@/lib/api/client";
import { useState, useCallback, useRef } from "react";
import type {
  ArticleResponse,
  ArticleCreateRequest,
  ArticleSaveRequest,
  AISuggestion,
  ContentMetrics,
  ContinueWritingResponse,
  TranslateResponse,
  LanguageCode,
  FactCheckResponse,
} from "@/lib/types/workbench";

export function useArticle(articleId: string | null) {
  return useQuery({
    queryKey: ["article", articleId],
    queryFn: () =>
      fetchFromApi<ArticleResponse>(`/api/workbench/articles/${articleId}`),
    enabled: !!articleId,
  });
}

export function useGenerateArticleFromOutline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { outlineId: string; headlineIndex?: number | null }) =>
      fetchFromApi<ArticleResponse>(
        "/api/workbench/articles/generate-from-outline",
        {
          method: "POST",
          body: JSON.stringify(data),
        }
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["article"] }),
  });
}

export function useCreateArticle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ArticleCreateRequest) =>
      fetchFromApi<ArticleResponse>("/api/workbench/articles", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["article"] }),
  });
}

export function useSaveArticle() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      articleId,
      ...data
    }: ArticleSaveRequest & { articleId: string }) =>
      fetchFromApi<ArticleResponse>(
        `/api/workbench/articles/${articleId}`,
        {
          method: "PUT",
          body: JSON.stringify(data),
        }
      ),
    onSuccess: (_, vars) =>
      qc.invalidateQueries({ queryKey: ["article", vars.articleId] }),
  });
}

export function useAISuggest() {
  return useMutation({
    mutationFn: ({ title, content }: { title: string; content: string }) =>
      fetchFromApi<{ aiSuggestions: AISuggestion[] }>(
        "/api/workbench/articles/suggest",
        {
          method: "POST",
          body: JSON.stringify({ title, content }),
        }
      ),
  });
}

export function useAIMetrics() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (articleId: string) =>
      fetchFromApi<{ metrics: ContentMetrics }>(
        `/api/workbench/articles/${articleId}/ai-metrics`,
        { method: "POST" }
      ),
    onSuccess: (_, articleId) =>
      qc.invalidateQueries({ queryKey: ["article", articleId] }),
  });
}

export function useAIContinueWriting() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (articleId: string) =>
      fetchFromApi<ContinueWritingResponse>(
        `/api/workbench/articles/${articleId}/ai-continue-writing`,
        { method: "POST" }
      ),
    onSuccess: (_, articleId) =>
      qc.invalidateQueries({ queryKey: ["article", articleId] }),
  });
}

export function useAITranslate() {
  return useMutation({
    mutationFn: ({ articleId, targetLanguage }: { articleId: string; targetLanguage: LanguageCode }) =>
      fetchFromApi<TranslateResponse>(
        `/api/workbench/articles/${articleId}/ai-translate`,
        {
          method: "POST",
          body: JSON.stringify({ targetLanguage }),
        }
      ),
  });
}

export function useAIFactCheck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (articleId: string) =>
      fetchFromApi<FactCheckResponse>(
        `/api/workbench/articles/${articleId}/ai-fact-check`,
        { method: "POST" }
      ),
    onSuccess: (_, articleId) =>
      qc.invalidateQueries({ queryKey: ["article", articleId] }),
  });
}

export function useGenerateArticleFromOutlineStream() {
  const [isPending, setIsPending] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  const mutate = useCallback(
    (
      data: { outlineId: string; headlineIndex?: number | null },
      callbacks: {
        onCreated: (data: { articleId: string; title: string; leadParagraph?: string }) => void;
        onChunk: (content: string) => void;
        onDone: (article: ArticleResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      setIsPending(true);
      controllerRef.current = fetchFromApiSSE(
        "/api/workbench/articles/generate-from-outline-stream",
        data,
        (event, eventData) => {
          if (event === "created") {
            callbacks.onCreated(eventData as { articleId: string; title: string; leadParagraph?: string });
          } else if (event === "chunk") {
            callbacks.onChunk((eventData as { content: string }).content);
          } else if (event === "done") {
            callbacks.onDone(eventData as ArticleResponse);
            setIsPending(false);
          } else if (event === "error") {
            callbacks.onError?.(new Error((eventData as { error: string }).error));
            setIsPending(false);
          }
        },
        (error: Error) => {
          callbacks.onError?.(error);
          setIsPending(false);
        }
      );
    },
    []
  );

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setIsPending(false);
  }, []);

  return { mutate, isPending, cancel };
}
