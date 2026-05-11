"use client";

import { useState, useEffect } from "react";
import type { KOLProfile } from "@/lib/types/kol";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Trash2, Power, PowerOff, Play } from "lucide-react";
import { useDeleteKOL, useToggleKOL, useCollectKOL } from "@/lib/api/queries/kol";
import { useQueryClient } from "@tanstack/react-query";

function formatCount(n?: number): string {
  if (!n) return "0";
  if (n >= 100_000_000) return `${(n / 100_000_000).toFixed(1)}亿`;
  if (n >= 10_000) return `${(n / 10_000).toFixed(1)}万`;
  return n.toLocaleString();
}

function timeAgo(date?: string): string {
  if (!date) return "从未同步";
  const diff = Date.now() - new Date(date).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return `${Math.floor(hours / 24)}天前`;
}

interface KOLCardProps {
  kol: KOLProfile;
}

export function KOLCard({ kol }: KOLCardProps) {
  const deleteKOL = useDeleteKOL();
  const toggleKOL = useToggleKOL();
  const collectKOL = useCollectKOL();
  const qc = useQueryClient();
  const [collecting, setCollecting] = useState(false);

  useEffect(() => {
    if (!collecting) return;
    const timer = setTimeout(() => {
      setCollecting(false);
      qc.invalidateQueries({ queryKey: ["kol"] });
    }, 90000);
    return () => clearTimeout(timer);
  }, [collecting, qc]);

  const handleCollect = () => {
    setCollecting(true);
    collectKOL.mutate(kol.sourceId, {
      onError: () => setCollecting(false),
    });
  };
  const platformLabel = kol.platform === "weibo" ? "微博" : "X";
  const cookieStatus = kol.cookieStatus || { active: 0, invalid: 0, expired: 0 };
  const hasCookie = cookieStatus.active > 0;

  return (
    <Card className="shadow-card">
      <CardContent className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-10 w-10 rounded-full bg-brand/10 flex items-center justify-center text-brand font-bold text-sm shrink-0">
              {kol.screenName.charAt(0)}
            </div>
            <div className="min-w-0">
              <div className="font-medium text-sm truncate">{kol.screenName}</div>
              <div className="text-xs text-muted-foreground truncate">
                @{kol.platformId}
              </div>
            </div>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${kol.platform === "x" ? "badge-platform-x" : "badge-platform-weibo"}`}>
            {platformLabel}
          </span>
        </div>

        {/* Stats */}
        {kol.followerCount != null && (
          <div className="flex gap-4 text-xs text-muted-foreground">
            <span>粉丝 {formatCount(kol.followerCount)}</span>
            <span>发帖 {formatCount(kol.postCount)}</span>
          </div>
        )}

        {/* Bio */}
        {kol.bio && (
          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">{kol.bio}</p>
        )}

        {/* Status row */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${kol.isActive && hasCookie ? "status-dot-active" : "bg-yellow-500"}`}
            />
            <span className="text-muted-foreground">
              {timeAgo(kol.lastSyncedAt)}
            </span>
            <span className="text-muted-foreground">
              Cookie: {hasCookie ? `${cookieStatus.active}可用` : "无"}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => toggleKOL.mutate({ kolId: kol.id, isActive: !kol.isActive })}
          >
            {kol.isActive ? (
              <PowerOff className="h-3 w-3" />
            ) : (
              <Power className="h-3 w-3" />
            )}
            {kol.isActive ? "暂停" : "启用"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleCollect}
            disabled={collecting}
          >
            <Play className="h-3 w-3" />
            {collecting ? "采集中" : "采集"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs text-destructive hover:text-destructive ml-auto"
            onClick={() => deleteKOL.mutate(kol.id)}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
