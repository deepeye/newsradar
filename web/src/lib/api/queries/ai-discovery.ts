"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { AIDiscoveryData } from "@/lib/types/ai-discovery";
import type { OutlineResponse } from "@/lib/types/outlines";

export function useAIDiscoveryData() {
  return useQuery({
    queryKey: ["ai-discovery"],
    queryFn: () => fetchFromApi<AIDiscoveryData>("/api/discovery"),
    staleTime: 5 * 60 * 1000, // 5 min — backend handles freshness via SWR
    gcTime: 10 * 60 * 1000, // keep cached data for 10 min
  });
}

export function useRefreshDiscovery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchFromApi<AIDiscoveryData>("/api/discovery/refresh", {
        method: "POST",
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["ai-discovery"], data);
    },
  });
}

interface GenerateOutlineRequest {
  clueIds: string[];
  additionalContext?: string;
}

export function useUpdateOrgConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { domains?: string[] | null; style?: string[] | null }) =>
      fetchFromApi<{ id: string; name: string; domains: string[]; style: string[] }>("/api/discovery/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-discovery"] });
    },
  });
}

export function useGenerateOutline() {
  return useMutation({
    mutationFn: (params: GenerateOutlineRequest) =>
      fetchFromApi<OutlineResponse>("/api/outlines/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clueIds: params.clueIds,
          additionalContext: params.additionalContext,
        }),
      }),
  });
}
