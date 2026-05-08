"use client";

import { useState } from "react";
import { useImportCookies } from "@/lib/api/queries/kol";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import type { KOLProfile } from "@/lib/types/kol";

interface CookieImportDialogProps {
  kol: KOLProfile | null;
  onClose: () => void;
}

export function CookieImportDialog({ kol, onClose }: CookieImportDialogProps) {
  const [cookieText, setCookieText] = useState("");
  const importCookies = useImportCookies();

  if (!kol) return null;

  const handleImport = async () => {
    if (!cookieText.trim()) return;
    const cookies = parseCookieString(cookieText);
    if (Object.keys(cookies).length === 0) return;

    try {
      await importCookies.mutateAsync({ kolId: kol.id, data: { cookies } });
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
          <h2 className="text-lg font-semibold">
            导入 Cookie - {kol.screenName}
          </h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Cookie 内容</label>
            <textarea
              value={cookieText}
              onChange={(e) => setCookieText(e.target.value)}
              placeholder={
                kol.platform === "weibo"
                  ? '从浏览器 DevTools > Application > Cookies 复制\n支持格式：SUB=xxx; SUBP=yyy\n或 JSON：{"SUB": "xxx", "SUBP": "yyy"}'
                  : '从浏览器 DevTools > Application > Cookies 复制\n支持格式：auth_token=xxx; ct0=yyy\n或 JSON：{"auth_token": "xxx", "ct0": "yyy"}'
              }
              rows={6}
              className="w-full px-3 py-2 rounded-lg border border-outline-variant/50 bg-background text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand/30 resize-none"
            />
            {kol.platform === "x" && (
              <p className="mt-1 text-xs text-tertiary">
                X Cookie 将在所有 X KOL 之间共享，只需导入一次即可
              </p>
            )}
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose} className="flex-1">
              取消
            </Button>
            <Button
              onClick={handleImport}
              disabled={!cookieText.trim() || importCookies.isPending}
              className="flex-1"
            >
              导入
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
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
