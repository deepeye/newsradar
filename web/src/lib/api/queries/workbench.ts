"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { WorkbenchData } from "@/lib/types/workbench";

export function useWorkbenchData() {
  return useQuery({
    queryKey: ["workbench"],
    queryFn: () => fetchFromApi<WorkbenchData>("/api/workbench/articles"),
  });
}
