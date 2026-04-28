"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { OutlinesData } from "@/lib/types/outlines";

export function useOutlinesData() {
  return useQuery({
    queryKey: ["outlines"],
    queryFn: () => fetchFromApi<OutlinesData>("/api/outlines"),
  });
}
