"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { AIDiscoveryData } from "@/lib/types/ai-discovery";
import type { OutlineResponse } from "@/lib/types/outlines";

export function useAIDiscoveryData() {
  return useQuery({
    queryKey: ["ai-discovery"],
    queryFn: () => fetchFromApi<AIDiscoveryData>("/api/discovery"),
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
