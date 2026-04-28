import { StatusTag } from "@/components/shared/status-tag";
import type { TrendingItem as TrendingItemType } from "@/lib/types/dashboard";
import { cn } from "@/lib/utils";

interface TrendingItemProps {
  item: TrendingItemType;
}

export function TrendingItem({ item }: TrendingItemProps) {
  return (
    <div className="flex items-center gap-3 py-2 px-1 group cursor-pointer hover:bg-accent/50 rounded-md transition-colors">
      <span
        className={cn(
          "flex items-center justify-center h-6 w-6 rounded text-xs font-bold shrink-0",
          item.rank <= 3
            ? "bg-brand text-white"
            : "bg-muted text-muted-foreground"
        )}
      >
        {item.rank}
      </span>
      <span className="flex-1 text-sm text-foreground group-hover:text-brand transition-colors line-clamp-1">
        {item.title}
      </span>
      {item.status && <StatusTag status={item.status} />}
      <span className="text-xs text-muted-foreground shrink-0">
        {item.heatValue}
      </span>
    </div>
  );
}
