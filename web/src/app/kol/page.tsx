"use client";

import { useState } from "react";
import { useKOLList, useKOLPosts } from "@/lib/api/queries/kol";
import { SectionHeader } from "@/components/shared/section-header";
import { KOLCard } from "@/components/kol/kol-card";
import { AddKOLDialog } from "@/components/kol/add-kol-dialog";
import { CookieImportDialog } from "@/components/kol/cookie-import-dialog";
import { KOLPosts } from "@/components/kol/kol-posts";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Users, Plus } from "lucide-react";
import type { KOLProfile } from "@/lib/types/kol";

const platformFilters = [
  { key: "", label: "全部" },
  { key: "weibo", label: "微博" },
  { key: "x", label: "X" },
];

export default function KOLPage() {
  const [platformFilter, setPlatformFilter] = useState("");
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [cookieKol, setCookieKol] = useState<KOLProfile | null>(null);
  const [selectedKolId, setSelectedKolId] = useState<string | null>(null);

  const { data, isLoading } = useKOLList(platformFilter || undefined);
  const { data: postsData } = useKOLPosts(selectedKolId || "");

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  const selectedKol = data.items.find((k) => k.id === selectedKolId);

  return (
    <div className="max-w-[1400px] mx-auto px-lg py-lg space-y-lg">
      {/* Header */}
      <div className="flex items-center justify-between">
        <SectionHeader
          icon={Users}
          title="KOL 监控"
          subtitle="跨平台意见领袖动态追踪"
        />
        <Button onClick={() => setAddDialogOpen(true)} className="gap-1">
          <Plus className="h-4 w-4" />
          添加 KOL
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        {platformFilters.map((f) => (
          <button
            key={f.key}
            onClick={() => setPlatformFilter(f.key)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              platformFilter === f.key
                ? "bg-brand/10 text-brand"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            }`}
          >
            {f.label}
            {f.key && (
              <Badge variant="ghost" className="ml-1 text-xs">
                {data.items.filter((k) => k.platform === f.key).length || ""}
              </Badge>
            )}
          </button>
        ))}
        <span className="ml-auto text-sm text-muted-foreground">
          共 {data.total} 个 KOL
        </span>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg">
        {/* KOL list */}
        <div className="lg:col-span-1 space-y-3 max-h-[calc(100vh-240px)] overflow-y-auto">
          {data.items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">暂无 KOL</p>
              <p className="text-xs mt-1">点击右上角按钮添加</p>
            </div>
          ) : (
            data.items.map((kol) => (
              <div
                key={kol.id}
                onClick={() => setSelectedKolId(kol.id)}
                className={`cursor-pointer rounded-xl transition-colors ${
                  selectedKolId === kol.id ? "ring-2 ring-brand/30" : ""
                }`}
              >
                <KOLCard kol={kol} onImportCookie={setCookieKol} />
              </div>
            ))
          )}
        </div>

        {/* Posts panel */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-outline-variant/30 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">
                {selectedKol ? `${selectedKol.screenName} 的最近动态` : "KOL 动态"}
              </h3>
              {postsData && (
                <span className="text-xs text-muted-foreground">
                  共 {postsData.total} 条
                </span>
              )}
            </div>
            {selectedKolId && postsData ? (
              <KOLPosts posts={postsData.items} />
            ) : (
              <div className="text-center py-12 text-muted-foreground text-sm">
                选择左侧 KOL 查看动态
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <AddKOLDialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} />
      <CookieImportDialog kol={cookieKol} onClose={() => setCookieKol(null)} />
    </div>
  );
}
