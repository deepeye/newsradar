import { Button } from "@/components/ui/button";
import { Sparkles, Trash2, Loader2 } from "lucide-react";
import { CopilotSuggestion } from "./copilot-suggestion";
import type { AISuggestion, ReferenceDoc } from "@/lib/types/workbench";

interface CopilotSidebarProps {
  suggestions: AISuggestion[];
  references: ReferenceDoc[];
  onRequestSuggestions: () => void;
  isRequestingSuggestions: boolean;
  onAcceptSuggestion: (suggestion: AISuggestion) => void;
  onRejectSuggestion: (suggestionId: string) => void;
  onClearSuggestions: () => void;
}

export function CopilotSidebar({
  suggestions,
  references,
  onRequestSuggestions,
  isRequestingSuggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
  onClearSuggestions,
}: CopilotSidebarProps) {
  return (
    <div className="w-[380px] shrink-0 flex flex-col h-full overflow-auto bg-sidebar rounded-md shadow-card">
      {/* Header */}
      <div className="p-md border-b border-sidebar-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand" />
          <h3 className="font-serif text-base font-semibold">AI Copilot</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-muted-foreground"
          onClick={onClearSuggestions}
          disabled={suggestions.length === 0}
        >
          <Trash2 className="h-3 w-3 mr-1" />
          清空建议
        </Button>
      </div>

      {/* Full polish button */}
      <div className="p-md">
        <Button
          className="w-full bg-brand hover:bg-brand-dark text-white text-sm"
          onClick={onRequestSuggestions}
          disabled={isRequestingSuggestions}
        >
          {isRequestingSuggestions ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4 mr-2" />
          )}
          {isRequestingSuggestions ? "AI 分析中..." : "全文润色建议"}
        </Button>
      </div>

      {/* Suggestions */}
      <div className="px-md pb-md space-y-3">
        {suggestions.map((s) => (
          <CopilotSuggestion
            key={s.id}
            suggestion={s}
            onAccept={() => onAcceptSuggestion(s)}
            onReject={() => onRejectSuggestion(s.id)}
          />
        ))}
      </div>

      {/* References */}
      <div className="p-md border-t border-sidebar-border">
        <h4 className="text-xs font-medium text-muted-foreground mb-2">参考资料</h4>
        <div className="space-y-2">
          {references.map((r) => (
            <div
              key={r.id}
              className="p-2 rounded bg-muted/50 text-xs"
            >
              <p className="font-medium text-foreground truncate">{r.title}</p>
              <p className="text-muted-foreground">
                {r.source} · {r.lastUpdated}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
