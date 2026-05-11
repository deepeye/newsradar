import { Button } from "@/components/ui/button";
import { Sparkles, Trash2, Loader2, ShieldCheck } from "lucide-react";
import { CopilotSuggestion } from "./copilot-suggestion";
import type { AISuggestion, ReferenceDoc, FactCheckResult } from "@/lib/types/workbench";

const statusStyles: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-700",
  unverified: "bg-amber-100 text-amber-700",
  contradicted: "bg-red-100 text-red-700",
};

const statusLabels: Record<string, string> = {
  verified: "已验证",
  unverified: "待验证",
  contradicted: "有矛盾",
};

interface CopilotSidebarProps {
  suggestions: AISuggestion[];
  references: ReferenceDoc[];
  onRequestSuggestions: () => void;
  isRequestingSuggestions: boolean;
  onAcceptSuggestion: (suggestion: AISuggestion) => void;
  onRejectSuggestion: (suggestionId: string) => void;
  onClearSuggestions: () => void;
  factCheckResults?: FactCheckResult[];
  onClearFactCheck?: () => void;
}

export function CopilotSidebar({
  suggestions,
  references,
  onRequestSuggestions,
  isRequestingSuggestions,
  onAcceptSuggestion,
  onRejectSuggestion,
  onClearSuggestions,
  factCheckResults,
  onClearFactCheck,
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
        {suggestions.map((s, i) => (
          <CopilotSuggestion
            key={s.id ?? i}
            suggestion={s}
            onAccept={() => onAcceptSuggestion(s)}
            onReject={() => onRejectSuggestion(s.id ?? String(i))}
          />
        ))}
      </div>

      {/* Fact-check results */}
      {factCheckResults && factCheckResults.length > 0 && (
        <div className="px-md pb-md space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-3.5 w-3.5 text-brand" />
              <h4 className="text-xs font-medium text-muted-foreground">事实核查</h4>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground"
              onClick={onClearFactCheck}
            >
              <Trash2 className="h-3 w-3 mr-1" />
              清空
            </Button>
          </div>
          {factCheckResults.map((r, i) => (
            <div key={i} className="p-2 rounded bg-muted/50 text-xs space-y-1.5">
              <div className="flex items-center gap-2">
                <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${statusStyles[r.status] || statusStyles.unverified}`}>
                  {statusLabels[r.status] || "待验证"}
                </span>
                <span className="text-muted-foreground/60">{r.type}/{r.confidence}</span>
              </div>
              <p className="font-medium text-foreground leading-snug">{r.claim}</p>
              {r.evidence && <p className="text-muted-foreground leading-snug">{r.evidence}</p>}
              {r.sourceUrls.length > 0 && (
                <div className="text-brand/70 text-[10px] truncate">
                  来源: {r.sourceUrls.join(" · ")}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* References */}
      <div className="p-md border-t border-sidebar-border">
        <h4 className="text-xs font-medium text-muted-foreground mb-2">参考资料</h4>
        <div className="space-y-2">
          {references.map((r, i) => (
            <div
              key={r.id ?? i}
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
