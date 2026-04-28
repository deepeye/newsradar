import { Button } from "@/components/ui/button";
import { Sparkles, RefreshCw } from "lucide-react";

interface LeadParagraphProps {
  paragraph: string;
}

export function LeadParagraph({ paragraph }: LeadParagraphProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand" />
          <h3 className="font-serif text-base font-semibold">5W1H 导语建议</h3>
        </div>
        <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">
          <RefreshCw className="h-3 w-3 mr-1" />
          重新生成导语
        </Button>
      </div>
      <div className="p-md bg-card rounded-md shadow-card border-l-2 border-brand">
        <p className="text-sm text-foreground/90 leading-relaxed">
          {paragraph}
        </p>
      </div>
    </div>
  );
}
