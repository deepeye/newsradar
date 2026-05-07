import { dashboardData } from "@/lib/mock/dashboard";
import { aiDiscoveryData } from "@/lib/mock/ai-discovery";
import { outlinesData } from "@/lib/mock/outlines";
import { mockArticle } from "@/lib/mock/workbench";
import { kolListData, kolPostsData } from "@/lib/mock/kol";

const USE_MOCK = !process.env.NEXT_PUBLIC_API_URL;

const mockDataMap: Record<string, unknown> = {
  "/api/dashboard": dashboardData,
  "/api/discovery": aiDiscoveryData,
  "/api/outlines": outlinesData,
  "/api/outlines/mock-outline-1": outlinesData.items[0],
  "/api/workbench/articles/mock-article-1": mockArticle,
  "/api/kol": kolListData,
  "/api/kol?platform=weibo": { total: 2, items: kolListData.items.filter((k) => k.platform === "weibo") },
  "/api/kol?platform=x": { total: 2, items: kolListData.items.filter((k) => k.platform === "x") },
};

const mockPostDataMap: Record<string, () => unknown> = {
  "/api/outlines/generate": () => outlinesData.items[0],
  "/api/discovery/refresh": () => aiDiscoveryData,
  "/api/workbench/articles": () => mockArticle,
  "/api/workbench/articles/mock-article-1/ai-suggest": () => ({
    aiSuggestions: mockArticle.aiSuggestions,
  }),
  "/api/workbench/articles/mock-article-1/ai-metrics": () => ({
    metrics: mockArticle.metrics,
  }),
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
    const delay = options?.method === "GET" || !options?.method ? 200 : 400;
    await new Promise((r) => setTimeout(r, delay));
    if (options?.method === "POST") {
      const handler = mockPostDataMap[path];
      if (handler) return handler() as T;
      // Fallback: match ai-suggest/ai-metrics by suffix for dynamic article IDs
      if (path.endsWith("/ai-suggest")) {
        return { aiSuggestions: mockArticle.aiSuggestions } as T;
      }
      if (path.endsWith("/ai-metrics")) {
        return { metrics: mockArticle.metrics } as T;
      }
      throw new Error(`No mock POST handler for ${path}`);
    }
    if (options?.method === "PUT") {
      // Mock PUT: return the article with updated content
      if (path.startsWith("/api/workbench/articles/")) {
        const body = options.body ? JSON.parse(options.body as string) : {};
        return {
          ...mockArticle,
          ...body,
          wordCount: body.content?.length ?? mockArticle.wordCount,
          completionPercent: Math.min(
            Math.round(((body.content?.length ?? mockArticle.wordCount) / mockArticle.targetWordCount) * 100),
            100
          ),
          lastSavedAt: new Date().toISOString(),
        } as T;
      }
      throw new Error(`No mock PUT handler for ${path}`);
    }
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