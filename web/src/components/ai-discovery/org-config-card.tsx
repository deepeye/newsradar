import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";
import type { OrgConfig } from "@/lib/types/ai-discovery";

interface OrgConfigCardProps {
  config: OrgConfig;
}

export function OrgConfigCard({ config }: OrgConfigCardProps) {
  return (
    <Card className="bg-card shadow-card border-0">
      <CardContent className="p-md">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4 text-brand" />
            <h3 className="font-serif text-base font-semibold">机构调性配置</h3>
          </div>
          <Button variant="outline" size="sm" className="text-xs border-outline-variant/40">
            更改配置
          </Button>
        </div>
        <div className="space-y-2">
          <div>
            <span className="text-xs text-muted-foreground">核心领域</span>
            <div className="flex items-center gap-2 mt-1">
              {config.domains.map((d) => (
                <span
                  key={d}
                  className="px-2.5 py-1 rounded bg-brand/10 text-brand text-xs font-medium"
                >
                  {d}
                </span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">风格</span>
            <div className="flex items-center gap-2 mt-1">
              {config.style.map((s) => (
                <span
                  key={s}
                  className="px-2.5 py-1 rounded bg-tertiary/10 text-tertiary text-xs font-medium"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
