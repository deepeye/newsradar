"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings, Check, X } from "lucide-react";
import { useUpdateOrgConfig } from "@/lib/api/queries/ai-discovery";
import type { OrgConfig } from "@/lib/types/ai-discovery";

interface OrgConfigCardProps {
  config: OrgConfig;
}

export function OrgConfigCard({ config }: OrgConfigCardProps) {
  const [editing, setEditing] = useState(false);
  const [domains, setDomains] = useState(config.domains);
  const [style, setStyle] = useState(config.style);
  const updateConfig = useUpdateOrgConfig();

  function startEditing() {
    setDomains(config.domains);
    setStyle(config.style);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
  }

  async function saveConfig() {
    await updateConfig.mutateAsync({ domains, style });
    setEditing(false);
  }

  return (
    <Card className="bg-card shadow-card border-0">
      <CardContent className="p-md">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-md bg-brand/10 flex items-center justify-center">
              <Settings className="h-3.5 w-3.5 text-brand" />
            </div>
            <h3 className="font-serif text-base font-semibold">机构调性配置</h3>
          </div>
          {editing ? (
            <div className="flex items-center gap-1">
              <Button variant="outline" size="sm" className="text-xs h-7" onClick={cancelEditing}>
                <X className="h-3 w-3" /> 取消
              </Button>
              <Button size="sm" className="text-xs h-7 bg-brand text-white" onClick={saveConfig} disabled={updateConfig.isPending}>
                <Check className="h-3 w-3" /> 保存
              </Button>
            </div>
          ) : (
            <Button variant="outline" size="sm" className="text-xs border-outline-variant/40" onClick={startEditing}>
              更改配置
            </Button>
          )}
        </div>
        <div className="space-y-2">
          {editing ? (
            <>
              <div>
                <span className="text-xs text-muted-foreground/70 uppercase tracking-wide">核心领域</span>
                <input
                  value={domains.join(", ")}
                  onChange={(e) => setDomains(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                  className="w-full mt-1 px-2 py-1.5 rounded border border-outline-variant/50 bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  placeholder="用逗号分隔，如：科技, 财经, 国际"
                />
              </div>
              <div>
                <span className="text-xs text-muted-foreground/70 uppercase tracking-wide">风格</span>
                <input
                  value={style.join(", ")}
                  onChange={(e) => setStyle(e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                  className="w-full mt-1 px-2 py-1.5 rounded border border-outline-variant/50 bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
                  placeholder="用逗号分隔，如：深度分析, 数据驱动, 独家视角"
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <span className="text-xs text-muted-foreground/70 uppercase tracking-wide">核心领域</span>
                <div className="flex items-center gap-2 mt-1">
                  {config.domains.map((d) => (
                    <span key={d} className="px-2.5 py-1 rounded bg-brand/10 text-brand text-xs font-medium">{d}</span>
                  ))}
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground/70 uppercase tracking-wide">风格</span>
                <div className="flex items-center gap-2 mt-1">
                  {config.style.map((s) => (
                    <span key={s} className="px-2.5 py-1 rounded bg-tertiary/10 text-tertiary text-xs font-medium">{s}</span>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}