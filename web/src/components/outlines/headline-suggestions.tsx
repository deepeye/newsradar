import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import type { HeadlineSuggestion } from "@/lib/types/outlines";

interface HeadlineSuggestionsProps {
  headlines: HeadlineSuggestion[];
}

export function HeadlineSuggestions({ headlines }: HeadlineSuggestionsProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-serif text-base font-semibold">备选标题</h3>
        <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">
          <RefreshCw className="h-3 w-3 mr-1" />
          换一批标题
        </Button>
      </div>
      <div className="space-y-2">
        {headlines.map((h, i) => (
          <Card key={h.id ?? `hl-${i}`} className="bg-card shadow-card border-0 hover:shadow-card-hover transition-shadow cursor-pointer">
            <CardContent className="p-md flex items-start gap-3">
              <span className="px-2 py-1 rounded bg-muted text-xs text-muted-foreground font-medium shrink-0">
                {h.style}
              </span>
              <p className="font-serif text-sm text-foreground leading-relaxed">
                {h.text}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
