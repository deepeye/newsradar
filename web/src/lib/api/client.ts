import { dashboardData } from "@/lib/mock/dashboard";
import { aiDiscoveryData } from "@/lib/mock/ai-discovery";
import { outlinesData } from "@/lib/mock/outlines";
import { mockArticle, mockContinueWriting, mockTranslate, mockFactCheck } from "@/lib/mock/workbench";
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
  "/api/workbench/articles/mock-article-1/ai-continue-writing": () => mockContinueWriting,
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
      if (path.endsWith("/ai-continue-writing")) {
        return mockContinueWriting as T;
      }
      if (path.endsWith("/ai-translate")) {
        const body = options.body ? JSON.parse(options.body as string) : {};
        return mockTranslate(body.targetLanguage || "en") as T;
      }
      if (path.endsWith("/ai-fact-check")) {
        return mockFactCheck as T;
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

/** SSE streaming fetch. Calls onEvent(event, data) for each parsed SSE event. Returns an abort controller. */
export function fetchFromApiSSE(
  path: string,
  body: Record<string, unknown>,
  onEvent: (event: string, data: unknown) => void,
  onError?: (error: Error) => void
): AbortController {
  const controller = new AbortController();

  if (USE_MOCK) {
    // Mock streaming: emit created event, then send body content as chunks
    const bodyContent = mockArticle.content || "";
    const chunks: string[] = [];
    const chunkSize = 80;
    for (let i = 0; i < bodyContent.length; i += chunkSize) {
      chunks.push(bodyContent.slice(i, i + chunkSize));
    }

    // Emit created event immediately
    onEvent("created", { articleId: mockArticle.id, title: mockArticle.title, leadParagraph: mockArticle.leadParagraph ?? "" });

    let idx = 0;
    const interval = setInterval(() => {
      if (controller.signal.aborted) {
        clearInterval(interval);
        return;
      }
      if (idx < chunks.length) {
        onEvent("chunk", { content: chunks[idx] });
        idx++;
      } else {
        clearInterval(interval);
        onEvent("done", mockArticle);
      }
    }, 50);

    return controller;
  }

  // Real SSE fetch
  const baseUrl = process.env.NEXT_PUBLIC_API_URL!;
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal: controller.signal,
  }).then(async (res) => {
    if (res.status === 401) {
      clearToken();
      window.location.href = "/login";
      return;
    }
    if (!res.ok) {
      onError?.(new Error(`API error: ${res.status}`));
      return;
    }

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split("\n");
      buffer = "";
      let currentEvent = "";
      let currentData = "";

      for (const line of lines) {
        if (line.startsWith("event:")) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          currentData = line.slice(5).trim();
        } else if (line === "" && currentEvent && currentData) {
          try {
            onEvent(currentEvent, JSON.parse(currentData));
          } catch {
            onEvent(currentEvent, currentData);
          }
          currentEvent = "";
          currentData = "";
        } else if (line !== "") {
          // Incomplete event, keep in buffer
          buffer = line + "\n";
        }
      }
    }
  }).catch((err) => {
    if (err.name !== "AbortError") onError?.(err);
  });

  return controller;
}