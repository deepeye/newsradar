interface EditorColumnProps {
  title: string;
  author: string;
  date: string;
  urgent: boolean;
  content: string;
}

export function EditorColumn({ title, author, date, urgent, content }: EditorColumnProps) {
  // Simple markdown-like rendering for MVP
  const paragraphs = content.split("\n\n").filter(Boolean);

  return (
    <div className="flex-1 min-w-0 overflow-auto bg-card rounded-md shadow-card">
      {/* Article header */}
      <div className="p-lg border-b border-outline-variant/20">
        <h1 className="font-serif text-xl font-bold text-foreground mb-3">
          {title}
        </h1>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            作者：{author}
          </span>
          <span>{date}</span>
          {urgent && (
            <span className="px-2 py-0.5 rounded bg-brand text-white font-medium">
              加急稿件
            </span>
          )}
        </div>
      </div>

      {/* Article content */}
      <div className="p-lg space-y-4">
        {paragraphs.map((p, i) => {
          // Quote block (starts with >)
          if (p.startsWith(">")) {
            return (
              <blockquote
                key={i}
                className="pl-4 py-2 border-l-2 border-brand italic text-foreground/80"
              >
                {p.replace(/^>\s*/, "").replace(/^"|"$/g, "").replace(/—.*$/, "")}
                <span className="block mt-1 text-xs text-muted-foreground not-italic">
                  {p.match(/—.*$/)?.[0] || ""}
                </span>
              </blockquote>
            );
          }

          // Heading (starts with ###)
          if (p.startsWith("### ")) {
            return (
              <h3 key={i} className="font-serif text-lg font-semibold text-foreground">
                {p.replace("### ", "")}
              </h3>
            );
          }

          // List (starts with 1. or -)
          if (p.match(/^\d+\.\s/) || p.startsWith("- ")) {
            const isNumbered = p.match(/^\d+\.\s/);
            const items = p.split("\n").filter(Boolean);
            return (
              <div key={i} className="space-y-2">
                {items.map((item, j) => {
                  const text = item.replace(/^\d+\.\s*/, "").replace(/^- /, "");
                  const isBold = text.startsWith("**") && text.endsWith("**");
                  const cleanText = text.replace(/\*\*/g, "");
                  return (
                    <div key={j} className="flex items-start gap-2">
                      <span className="text-xs text-muted-foreground mt-0.5 shrink-0">
                        {isNumbered ? `${j + 1}.` : "•"}
                      </span>
                      <p className="text-sm text-foreground/90">
                        {isBold ? (
                          <>
                            <strong className="font-medium">{cleanText.split(":")[0]}:</strong>
                            {cleanText.split(":").slice(1).join(":")}
                          </>
                        ) : (
                          cleanText
                        )}
                      </p>
                    </div>
                  );
                })}
              </div>
            );
          }

          // Placeholder (starts with [此处待补充)
          if (p.startsWith("[此处待补充")) {
            return (
              <div
                key={i}
                className="p-3 rounded-md bg-brand/5 border border-brand/20 text-xs text-muted-foreground italic"
              >
                {p}
              </div>
            );
          }

          // Regular paragraph
          return (
            <p key={i} className="text-sm text-foreground/90 leading-relaxed">
              {p}
            </p>
          );
        })}
      </div>
    </div>
  );
}