import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { OutlineSection as OutlineSectionType } from "@/lib/types/outlines";

interface OutlineSectionProps {
  section: OutlineSectionType;
}

export function OutlineSectionView({ section }: OutlineSectionProps) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <Card className="bg-card shadow-card hover:shadow-card-hover transition-shadow border-0">
      <CardContent className="p-0">
        {/* Header */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center gap-3 py-3 px-md hover:bg-accent/50 transition-colors"
        >
          <span className="flex items-center justify-center h-6 w-6 rounded-full bg-brand text-white text-xs font-bold">
            {section.number}
          </span>
          <span className="font-serif text-sm font-semibold text-foreground text-left flex-1">
            {section.title}
          </span>
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          {isOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>

        {/* Content */}
        {isOpen && (
          <div className="px-md pb-md pl-12 space-y-2">
            {section.items.map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-3 p-3 bg-card/60 rounded-md group hover:bg-card transition-colors"
              >
                <span className="text-xs text-muted-foreground mt-0.5 font-mono">
                  {section.number}.{item.id.split("-")[1]}
                </span>
                <p className="flex-1 text-sm text-foreground/90">{item.content}</p>
                {item.hasAIRewrite && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-brand opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                  >
                    <Sparkles className="h-3 w-3 mr-1" />
                    AI 改写
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface OutlineSectionListProps {
  sections: OutlineSectionType[];
}

export function OutlineSectionList({ sections }: OutlineSectionListProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="h-4 w-4 text-brand" />
        <h3 className="font-serif text-base font-semibold">结构化大纲框架</h3>
      </div>
      <div className="space-y-2">
        {sections.map((section) => (
          <OutlineSectionView key={section.id} section={section} />
        ))}
      </div>
    </div>
  );
}