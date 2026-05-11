"use client";

import { useRef, useEffect } from "react";

interface EditorColumnProps {
  title: string;
  author: string;
  date: string;
  urgent: boolean;
  content: string;
  onContentChange: (content: string) => void;
}

export function EditorColumn({
  title,
  author,
  date,
  urgent,
  content,
  onContentChange,
}: EditorColumnProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea to fit content
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = el.scrollHeight + "px";
    }
  }, [content]);

  return (
    <div className="flex-1 min-w-0 overflow-auto bg-card rounded-md shadow-card flex flex-col">
      {/* Article header */}
      <div className="p-lg border-b border-outline-variant/20 shrink-0">
        <h1 className="font-serif text-xl font-bold text-foreground mb-3">
          {title}
        </h1>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>作者：{author}</span>
          <span>{date}</span>
          {urgent && (
            <span className="px-2 py-0.5 rounded bg-brand text-white font-medium">
              加急稿件
            </span>
          )}
        </div>
      </div>

      {/* Editable content area */}
      <textarea
        ref={textareaRef}
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        className="editor-textarea flex-1 w-full p-lg resize-none bg-transparent text-sm text-foreground/90 leading-relaxed focus:outline-none placeholder:text-muted-foreground/40"
        placeholder="开始撰写文章..."
        spellCheck={false}
      />
    </div>
  );
}
