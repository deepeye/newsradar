import type { KOLPost } from "@/lib/types/dashboard";
import { ThumbsUp, Share2, MessageCircle } from "lucide-react";

interface KOLPostProps {
  post: KOLPost;
}

function formatNumber(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export function KOLPost({ post }: KOLPostProps) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="flex items-center gap-2 mb-1.5">
        <div className="h-6 w-6 rounded-full bg-brand/15 flex items-center justify-center text-brand text-[10px] font-bold">
          {post.author.charAt(0)}
        </div>
        <span className="text-sm font-medium text-foreground">
          {post.author}
        </span>
        {post.verified && (
          <span className="text-[10px] bg-tertiary/10 text-tertiary px-1.5 py-0.5 rounded font-medium">
            V
          </span>
        )}
        <span className="text-xs text-muted-foreground ml-auto">
          {post.timeAgo}
        </span>
      </div>
      <p className="text-sm text-foreground/90 leading-relaxed line-clamp-2 mb-2">
        {post.content}
      </p>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <ThumbsUp className="h-3 w-3" />
          {formatNumber(post.likes)}
        </span>
        <span className="flex items-center gap-1">
          <Share2 className="h-3 w-3" />
          {formatNumber(post.shares)}
        </span>
        <span className="flex items-center gap-1">
          <MessageCircle className="h-3 w-3" />
          {formatNumber(post.comments)}
        </span>
      </div>
    </div>
  );
}
