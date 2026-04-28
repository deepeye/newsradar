import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, ArrowRight } from "lucide-react";
import type { AITopicSuggestion } from "@/lib/types/dashboard";

interface AIAssistantCardProps {
  suggestions: AITopicSuggestion[];
}

export function AIAssistantCard({ suggestions }: AIAssistantCardProps) {
  return (
    <Card className="bg-gradient-to-r from-brand/5 to-tertiary/5 shadow-card border border-brand/10">
      <CardContent className="p-lg">
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-center justify-center h-8 w-8 rounded-md bg-brand text-white">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h3 className="font-serif text-base font-semibold">今日推荐选题</h3>
            <p className="text-xs text-muted-foreground">AI 跨平台关联分析</p>
          </div>
        </div>
        <div className="space-y-3 mb-4">
          {suggestions.map((s) => (
            <div key={s.id} className="p-3 rounded-md bg-card/80">
              <p className="text-sm font-medium text-foreground mb-1">
                {s.title}
              </p>
              <p className="text-xs text-muted-foreground">{s.description}</p>
            </div>
          ))}
        </div>
        <Button className="w-full bg-brand hover:bg-brand-dark text-white">
          一键生成提纲
          <ArrowRight className="h-4 w-4 ml-1" />
        </Button>
      </CardContent>
    </Card>
  );
}
