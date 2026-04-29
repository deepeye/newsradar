"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { AIDiscoveryData } from "@/lib/types/ai-discovery";

export function useAIDiscoveryData() {
  return useQuery({
    queryKey: ["ai-discovery"],
    queryFn: () => fetchFromApi<AIDiscoveryData>("/api/discovery"),
  });
}
