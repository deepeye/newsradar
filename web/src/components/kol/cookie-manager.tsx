"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchFromApi } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Trash2, Cookie } from "lucide-react";

interface PlatformCookie {
  platform: string;
  cookies: Array<{
    id: string;
    name: string;
    status: string;
    created_at: string;
    last_used_at: string | null;
  }>;
}

function usePlatformCookies() {
  return useQuery({
    queryKey: ["kol-cookies"],
    queryFn: () => fetchFromApi<PlatformCookie[]>("/api/kol/cookies"),
  });
}

function useImportPlatformCookie() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      platform,
      cookies,
    }: {
      platform: string;
      cookies: Record<string, string>;
    }) =>
      fetchFromApi(`/api/kol/cookies/import?platform=${encodeURIComponent(platform)}`, {
        method: "POST",
        body: JSON.stringify({ cookies }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kol-cookies"] }),
  });
}

function useDeletePlatformCookie() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (cookieId: string) =>
      fetchFromApi(`/api/kol/cookies/${cookieId}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kol-cookies"] }),
  });
}

function parseCookieString(text: string): Record<string, string> {
  text = text.trim();
  if (text.startsWith("{")) {
    try {
      return JSON.parse(text);
    } catch {
      // Fall through
    }
  }
  const cookies: Record<string, string> = {};
  const pairs = text.split(";").map((s) => s.trim()).filter(Boolean);
  for (const pair of pairs) {
    const eq = pair.indexOf("=");
    if (eq > 0) {
      const key = pair.slice(0, eq).trim();
      const value = pair.slice(eq + 1).trim();
      cookies[key] = value;
    }
  }
  return cookies;
}

export function CookieManager() {
  const { data, isLoading } = usePlatformCookies();
  const importCookie = useImportPlatformCookie();
  const deleteCookie = useDeletePlatformCookie();
  const [importingPlatform, setImportingPlatform] = useState<string | null>(null);
  const [cookieText, setCookieText] = useState("");

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  const handleImport = async (platform: string) => {
    if (!cookieText.trim()) return;
    const cookies = parseCookieString(cookieText);
    if (Object.keys(cookies).length === 0) return;

    try {
      await importCookie.mutateAsync({ platform, cookies });
      setCookieText("");
      setImportingPlatform(null);
    } catch {
      // Error handled by mutation
    }
  };

  const platformLabels: Record<string, string> = {
    x: "X (Twitter)",
    weibo: "微博",
  };

  const platformIcons: Record<string, string> = {
    x: "𝕏",
    weibo: "微",
  };

  return (
    <div className="space-y-lg">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
        {data.map((platform, i) => (
          <Card key={`${platform.platform}-${i}`}>
            <CardContent className="space-y-4">
              {/* Platform Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-brand/20 flex items-center justify-center text-brand font-bold text-sm">
                    {platformIcons[platform.platform] || "?"}
                  </div>
                  <div>
                    <div className="font-medium">{platformLabels[platform.platform] || platform.platform}</div>
                    <div className="text-xs text-muted-foreground">
                      {platform.cookies.filter((c) => c.status === "active").length} 个可用 Cookie
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setImportingPlatform(platform.platform)}
                >
                  <Cookie className="h-3 w-3 mr-1" />
                  导入Cookie
                </Button>
              </div>

              {/* Cookie List */}
              <div className="space-y-2">
                {platform.cookies.length === 0 ? (
                  <div className="text-center py-4 text-muted-foreground text-sm">
                    暂无Cookie，点击上方按钮导入
                  </div>
                ) : (
                  platform.cookies.map((cookie) => (
                    <div
                      key={cookie.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-accent/50"
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className={`h-2 w-2 rounded-full ${
                            cookie.status === "active"
                              ? "bg-green-500"
                              : cookie.status === "invalid"
                              ? "bg-red-500"
                              : "bg-yellow-500"
                          }`}
                        />
                        <div>
                          <div className="text-sm font-medium">{cookie.name}</div>
                          <div className="text-xs text-muted-foreground">
                            状态: {cookie.status} · 创建于{" "}
                            {new Date(cookie.created_at).toLocaleDateString("zh-CN")}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                        onClick={() => deleteCookie.mutate(cookie.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  ))
                )}
              </div>

              {/* Import Dialog */}
              {importingPlatform === platform.platform && (
                <div className="p-4 rounded-lg bg-accent/50 space-y-3">
                  <label className="block text-sm font-medium">Cookie 内容</label>
                  <textarea
                    value={cookieText}
                    onChange={(e) => setCookieText(e.target.value)}
                    placeholder='从浏览器 DevTools → Application → Cookies 复制完整 Cookie 字符串\n例如：auth_token=xxx; ct0=yyy; twid=u%3D123; kdt=abc\n也支持 JSON 格式：{"auth_token": "xxx", "ct0": "yyy"}'
                    rows={5}
                    className="w-full px-3 py-2 rounded-lg border border-outline-variant/50 bg-background text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand/30 resize-none"
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setImportingPlatform(null)}
                    >
                      取消
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleImport(platform.platform)}
                      disabled={!cookieText.trim() || importCookie.isPending}
                    >
                      {importCookie.isPending ? "导入中..." : "导入"}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}