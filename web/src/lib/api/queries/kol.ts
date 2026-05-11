"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type {
  KOLProfile,
  KOLListResponse,
  KOLPostListResponse,
  KOLCreateRequest,
  KOLCookieImportRequest,
} from "@/lib/types/kol";

export function useKOLList(platform?: string) {
  return useQuery({
    queryKey: ["kol", platform],
    queryFn: () => {
      const params = platform ? `?platform=${platform}` : "";
      return fetchFromApi<KOLListResponse>(`/api/kol${params}`);
    },
  });
}

export function useKOLPosts(kolId: string, page = 1) {
  return useQuery({
    queryKey: ["kol", kolId, "posts", page],
    queryFn: () =>
      fetchFromApi<KOLPostListResponse>(
        `/api/kol/${kolId}/posts?page=${page}&pageSize=10`
      ),
    enabled: !!kolId,
  });
}

export function useCreateKOL() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: KOLCreateRequest) =>
      fetchFromApi<KOLProfile>("/api/kol", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kol"] }),
  });
}

export function useDeleteKOL() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (kolId: string) =>
      fetchFromApi(`/api/kol/${kolId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kol"] }),
  });
}

export function useImportCookies() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      kolId,
      data,
    }: {
      kolId: string;
      data: KOLCookieImportRequest;
    }) =>
      fetchFromApi(`/api/kol/${kolId}/cookies`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kol"] }),
  });
}

export function useToggleKOL() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      kolId,
      isActive,
    }: {
      kolId: string;
      isActive: boolean;
    }) =>
      fetchFromApi<KOLProfile>(`/api/kol/${kolId}`, {
        method: "PATCH",
        body: JSON.stringify({ isActive }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kol"] }),
  });
}

export function useCollectAllKOLs() {
  return useMutation({
    mutationFn: () =>
      fetchFromApi<{ detail: string; count: number }>("/api/kol/collect", {
        method: "POST",
      }),
  });
}

export function useCollectKOL() {
  return useMutation({
    mutationFn: (sourceId: string) =>
      fetchFromApi<{ detail: string; count: number }>(
        `/api/kol/${sourceId}/collect`,
        { method: "POST" }
      ),
  });
}
