interface EditorStatusBarProps {
  wordCount: number;
  targetWordCount: number;
  completionPercent: number;
  lastSaved: string;
}

export function EditorStatusBar({
  wordCount,
  targetWordCount,
  completionPercent,
  lastSaved,
}: EditorStatusBarProps) {
  return (
    <div className="flex items-center justify-between py-2 px-3 bg-muted/50 rounded-md text-xs">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">完成度</span>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-24 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full bg-brand rounded-full transition-all"
                style={{ width: `${completionPercent}%` }}
              />
            </div>
            <span className="font-medium text-brand">{completionPercent}%</span>
          </div>
        </div>
        <div className="text-muted-foreground">
          字数：<span className="font-medium text-foreground">{wordCount}</span> / {targetWordCount}
        </div>
      </div>
      <div className="text-muted-foreground">
        {lastSaved ? `自动保存于 ${lastSaved}` : "未保存"}
      </div>
    </div>
  );
}