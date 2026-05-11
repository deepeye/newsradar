import { Button } from "@/components/ui/button";
import {
  Bold,
  Italic,
  Underline,
  List,
  ListOrdered,
  Quote,
  ImageIcon,
  Link2,
  PenLine,
  Loader2,
} from "lucide-react";

const toolbarItems = [
  { icon: Bold, label: "加粗" },
  { icon: Italic, label: "斜体" },
  { icon: Underline, label: "下划线" },
  { icon: List, label: "无序列表" },
  { icon: ListOrdered, label: "有序列表" },
  { icon: Quote, label: "引用" },
  { icon: ImageIcon, label: "插入图片" },
  { icon: Link2, label: "插入链接" },
];

interface EditorToolbarProps {
  onContinueWriting?: () => void;
  isContinuingWriting?: boolean;
}

export function EditorToolbar({ onContinueWriting, isContinuingWriting }: EditorToolbarProps) {
  return (
    <div className="flex items-center gap-1 py-2 px-3 bg-card rounded-md shadow-card border-b border-outline-variant/20">
      {toolbarItems.map((item, i) => (
        <Button
          key={i}
          variant="ghost"
          size="sm"
          className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground hover:bg-accent"
          title={item.label}
        >
          <item.icon className="h-4 w-4" />
        </Button>
      ))}
      <div className="w-px h-5 bg-outline-variant/30 mx-1" />
      <Button
        variant="ghost"
        size="sm"
        className="text-xs text-muted-foreground hover:text-foreground"
      >
        清除格式
      </Button>
      {onContinueWriting && (
        <Button
          variant="outline"
          size="sm"
          onClick={onContinueWriting}
          disabled={isContinuingWriting}
          className="ml-auto text-xs border-brand/40 text-brand hover:bg-brand/10 hover:border-brand/60"
        >
          {isContinuingWriting ? (
            <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
          ) : (
            <PenLine className="h-3.5 w-3.5 mr-1" />
          )}
          {isContinuingWriting ? "续写中..." : "续写"}
        </Button>
      )}
    </div>
  );
}