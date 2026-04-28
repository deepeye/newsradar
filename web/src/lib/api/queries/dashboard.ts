"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import type { DashboardData } from "@/lib/types/dashboard";

export function useDashboardData() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => fetchFromApi<DashboardData>("/api/dashboard"),
  });
}
