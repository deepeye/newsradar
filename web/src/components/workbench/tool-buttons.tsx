import { Button } from "@/components/ui/button";
import { Languages, ShieldCheck, Paintbrush, FileText } from "lucide-react";

const tools = [
  { icon: Languages, label: "一键翻译" },
  { icon: ShieldCheck, label: "事实核查" },
  { icon: Paintbrush, label: "格式统一" },
  { icon: FileText, label: "生成摘要" },
];

export function ToolButtons() {
  return (
    <div className="flex items-center gap-2 p-3 bg-card rounded-md shadow-card">
      {tools.map((tool) => (
        <Button
          key={tool.label}
          variant="outline"
          size="sm"
          className="text-xs border-outline-variant/40 text-muted-foreground hover:text-foreground hover:border-brand/30"
        >
          <tool.icon className="h-3.5 w-3.5 mr-1" />
          {tool.label}
        </Button>
      ))}
    </div>
  );
}