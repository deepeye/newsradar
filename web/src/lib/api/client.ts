import { dashboardData } from "@/lib/mock/dashboard";
import { aiDiscoveryData } from "@/lib/mock/ai-discovery";
import { outlinesData } from "@/lib/mock/outlines";
import { workbenchData } from "@/lib/mock/workbench";

const USE_MOCK = !process.env.NEXT_PUBLIC_API_URL;

const mockDataMap: Record<string, unknown> = {
  "/api/dashboard": dashboardData,
  "/api/discovery": aiDiscoveryData,
  "/api/outlines": outlinesData,
  "/api/workbench": workbenchData,
};

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string): void {
  localStorage.setItem("access_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("access_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function fetchFromApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 200));
    const data = mockDataMap[path];
    if (!data) throw new Error(`No mock data for ${path}`);
    return data as T;
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL!;
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}