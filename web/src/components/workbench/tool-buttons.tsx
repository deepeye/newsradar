import { Button } from "@/components/ui/button";
import { Languages, ShieldCheck, Paintbrush, FileText, Loader2 } from "lucide-react";

interface ToolButtonsProps {
  onAnalyzeMetrics: () => void;
  isAnalyzing: boolean;
}

const tools = [
  { icon: Languages, label: "一键翻译", disabled: true },
  { icon: ShieldCheck, label: "事实核查", disabled: true },
  { icon: Paintbrush, label: "格式统一", disabled: true },
];

export function ToolButtons({ onAnalyzeMetrics, isAnalyzing }: ToolButtonsProps) {
  return (
    <div className="flex items-center gap-2 p-3 bg-card rounded-md shadow-card">
      {tools.map((tool) => (
        <Button
          key={tool.label}
          variant="outline"
          size="sm"
          disabled={tool.disabled}
          className="text-xs border-outline-variant/40 text-muted-foreground hover:text-foreground hover:border-brand/30"
        >
          <tool.icon className="h-3.5 w-3.5 mr-1" />
          {tool.label}
        </Button>
      ))}
      <Button
        variant="outline"
        size="sm"
        onClick={onAnalyzeMetrics}
        disabled={isAnalyzing}
        className="text-xs border-outline-variant/40 text-muted-foreground hover:text-foreground hover:border-brand/30"
      >
        {isAnalyzing ? (
          <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
        ) : (
          <FileText className="h-3.5 w-3.5 mr-1" />
        )}
        AI 分析
      </Button>
    </div>
  );
}
