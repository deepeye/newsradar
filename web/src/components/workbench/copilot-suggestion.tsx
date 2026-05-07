import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X } from "lucide-react";
import type { AISuggestion } from "@/lib/types/workbench";

const typeColors: Record<AISuggestion["type"], string> = {
  grammar: "bg-emerald-100 text-emerald-700",
  style: "bg-brand/10 text-brand",
  fact: "bg-tertiary/10 text-tertiary",
};

interface CopilotSuggestionProps {
  suggestion: AISuggestion;
  onAccept: () => void;
  onReject: () => void;
}

export function CopilotSuggestion({ suggestion, onAccept, onReject }: CopilotSuggestionProps) {
  return (
    <div className="p-3 rounded-md bg-card shadow-card space-y-2">
      <div className="flex items-center justify-between">
        <Badge className={`${typeColors[suggestion.type]} text-xs`}>
          {suggestion.type === "grammar" ? "语法" : suggestion.type === "style" ? "风格" : "事实"}
        </Badge>
      </div>
      <p className="text-xs text-muted-foreground">{suggestion.reason}</p>
      <div className="space-y-1.5">
        <p className="text-sm text-foreground/60 line-through decoration-muted-foreground/30">
          {suggestion.original}
        </p>
        <p className="text-sm text-brand font-medium">
          {suggestion.suggested}
        </p>
      </div>
      <div className="flex items-center gap-2 pt-1">
        <Button
          size="sm"
          className="h-7 text-xs bg-brand hover:bg-brand-dark text-white"
          onClick={onAccept}
        >
          <Check className="h-3 w-3 mr-1" />
          替换原句
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs text-muted-foreground"
          onClick={onReject}
        >
          <X className="h-3 w-3 mr-1" />
          拒绝
        </Button>
      </div>
    </div>
  );
}
