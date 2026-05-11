"use client";

import { useState } from "react";

interface HeadlineSuggestion {
  style: string;
  text: string;
}

interface HeadlineSelectorProps {
  headlines: HeadlineSuggestion[];
  defaultTitle: string;
  onSelect: (headlineIndex: number | null, selectedTitle: string) => void;
  isGenerating: boolean;
}

export function HeadlineSelector({
  headlines,
  defaultTitle,
  onSelect,
  isGenerating,
}: HeadlineSelectorProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-card rounded-lg shadow-lg p-6 max-w-lg w-full mx-4">
        <h2 className="text-lg font-semibold mb-2">选择文章标题</h2>
        <p className="text-sm text-muted-foreground mb-4">
          AI 生成了多个标题建议，请选择一个作为文章标题，或使用原始标题。
        </p>

        <div className="space-y-2 mb-4">
          {/* Default title option */}
          <button
            onClick={() => setSelectedIndex(null)}
            className={`w-full text-left px-4 py-3 rounded-md border transition-colors ${
              selectedIndex === null
                ? "border-brand bg-brand/10 text-brand"
                : "border-border hover:border-brand/50"
            }`}
          >
            <div className="text-xs text-muted-foreground mb-1">原始标题</div>
            <div className="font-medium">{defaultTitle}</div>
          </button>

          {/* Headline suggestions */}
          {headlines.map((hl, i) => (
            <button
              key={i}
              onClick={() => setSelectedIndex(i)}
              className={`w-full text-left px-4 py-3 rounded-md border transition-colors ${
                selectedIndex === i
                  ? "border-brand bg-brand/10 text-brand"
                  : "border-border hover:border-brand/50"
              }`}
            >
              <div className="text-xs text-muted-foreground mb-1">
                {hl.style}
              </div>
              <div className="font-medium">{hl.text}</div>
            </button>
          ))}
        </div>

        <button
          onClick={() => onSelect(selectedIndex, selectedIndex !== null ? headlines[selectedIndex].text : defaultTitle)}
          disabled={isGenerating}
          className="w-full px-4 py-2 rounded-md bg-brand text-brand-foreground font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? "正在生成初稿..." : "确认并生成初稿"}
        </button>
      </div>
    </div>
  );
}