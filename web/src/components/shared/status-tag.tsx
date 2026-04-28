import { cn } from "@/lib/utils";
import type { TrendStatus } from "@/lib/types";

interface StatusTagProps {
  status: TrendStatus;
  className?: string;
}

const statusConfig: Record<TrendStatus, { label: string; className: string }> = {
  explosive: { label: "爆", className: "bg-brand text-white" },
  new: { label: "新", className: "bg-tertiary text-white" },
  rank_up: { label: "↑", className: "bg-emerald-100 text-emerald-700" },
  rank_down: { label: "↓", className: "bg-red-100 text-red-600" },
  stable: { label: "—", className: "bg-gray-100 text-gray-500" },
};

export function StatusTag({ status, className }: StatusTagProps) {
  const config = statusConfig[status];
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center min-w-[20px] h-5 px-1 rounded text-xs font-bold leading-none",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}
