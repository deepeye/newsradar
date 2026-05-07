"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type {
  ArticleResponse,
  ArticleCreateRequest,
  ArticleSaveRequest,
  AISuggestion,
  ContentMetrics,
} from "@/lib/types/workbench";

export function useArticle(articleId: string | null) {
  return useQuery({
    queryKey: ["article", articleId],
    queryFn: () =>
      fetchFromApi<ArticleResponse>(`/api/workbench/articles/${articleId}`),
    enabled: !!articleId,
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
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (articleId: string) =>
      fetchFromApi<{ aiSuggestions: AISuggestion[] }>(
        `/api/workbench/articles/${articleId}/ai-suggest`,
        { method: "POST" }
      ),
    onSuccess: (_, articleId) =>
      qc.invalidateQueries({ queryKey: ["article", articleId] }),
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
