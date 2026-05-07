"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { OutlineListResponse, OutlineResponse } from "@/lib/types/outlines";

export function useOutlinesList() {
  return useQuery({
    queryKey: ["outlines"],
    queryFn: () => fetchFromApi<OutlineListResponse>("/api/outlines"),
  });
}

export function useOutline(id: string | null) {
  return useQuery({
    queryKey: ["outlines", id],
    queryFn: () => fetchFromApi<OutlineResponse>(`/api/outlines/${id}`),
    enabled: !!id,
  });
}
