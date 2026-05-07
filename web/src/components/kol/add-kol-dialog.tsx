"use client";

import { useState } from "react";
import { useCreateKOL } from "@/lib/api/queries/kol";
import { Button } from "@/components/ui/button";
import type { KOLCreateRequest } from "@/lib/types/kol";
import { Plus, X } from "lucide-react";

interface AddKOLDialogProps {
  open: boolean;
  onClose: () => void;
}

export function AddKOLDialog({ open, onClose }: AddKOLDialogProps) {
  const [platform, setPlatform] = useState<"weibo" | "x">("weibo");
  const [platformId, setPlatformId] = useState("");
  const [screenName, setScreenName] = useState("");
  const [cookieText, setCookieText] = useState("");
  const createKOL = useCreateKOL();

  if (!open) return null;

  const handleSubmit = async () => {
    if (!platformId.trim() || !screenName.trim()) return;

    let cookies: Record<string, string> | undefined;
    if (cookieText.trim()) {
      cookies = parseCookieString(cookieText);
    }

    const data: KOLCreateRequest = {
      platform,
      platformId: platformId.trim(),
      screenName: screenName.trim(),
      cookies,
    };

    try {
      await createKOL.mutateAsync(data);
      setPlatformId("");
      setScreenName("");
      setCookieText("");
      onClose();
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card rounded-xl p-6 w-full max-w-[448px] shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">添加 KOL</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Platform */}
          <div>
            <label className="block text-sm font-medium mb-1">平台</label>
            <div className="flex gap-2">
              <button
                onClick={() => setPlatform("weibo")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  platform === "weibo"
                    ? "bg-brand text-brand-foreground"
                    : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
              >
                微博
              </button>
              <button
                onClick={() => setPlatform("x")}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  platform === "x"
                    ? "bg-brand text-brand-foreground"
                    : "bg-muted text-muted-foreground hover:bg-accent"
                }`}
              >
                X (Twitter)
              </button>
            </div>
          </div>

          {/* Platform ID */}
          <div>
            <label className="block text-sm font-medium mb-1">
              {platform === "weibo" ? "微博 UID" : "X 用户名"}
            </label>
            <input
              type="text"
              value={platformId}
              onChange={(e) => setPlatformId(e.target.value)}
              placeholder={platform === "weibo" ? "如：1192329374" : "如：elonmusk"}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant/50 bg-background text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            />
          </div>

          {/* Screen Name */}
          <div>
            <label className="block text-sm font-medium mb-1">显示名称</label>
            <input
              type="text"
              value={screenName}
              onChange={(e) => setScreenName(e.target.value)}
              placeholder="如：胡锡进"
              className="w-full px-3 py-2 rounded-lg border border-outline-variant/50 bg-background text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            />
          </div>

          {/* Cookie (optional) */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Cookie <span className="text-muted-foreground font-normal">(可选)</span>
            </label>
            <textarea
              value={cookieText}
              onChange={(e) => setCookieText(e.target.value)}
              placeholder={
                platform === "weibo"
                  ? "从浏览器 DevTools 复制 Cookie，支持 SUB=xxx; 格式或 JSON 格式"
                  : "从浏览器 DevTools 复制 Cookie，支持 key=value; 格式或 JSON 格式"
              }
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant/50 bg-background text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand/30 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <Button variant="outline" onClick={onClose} className="flex-1">
              取消
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!platformId.trim() || !screenName.trim() || createKOL.isPending}
              className="flex-1"
            >
              <Plus className="h-4 w-4 mr-1" />
              添加
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function parseCookieString(text: string): Record<string, string> {
  text = text.trim();
  // Try JSON first
  if (text.startsWith("{")) {
    try {
      return JSON.parse(text);
    } catch {
      // Fall through to cookie string parsing
    }
  }
  // Parse "key=value; key2=value2" format
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
