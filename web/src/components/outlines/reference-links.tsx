import { ExternalLink, Link2 } from "lucide-react";
import type { ReferenceLink } from "@/lib/types/outlines";

interface ReferenceLinksProps {
  references: ReferenceLink[];
}

export function ReferenceLinks({ references }: ReferenceLinksProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Link2 className="h-4 w-4 text-brand" />
        <h3 className="font-serif text-base font-semibold">参考素材链接</h3>
      </div>
      <div className="space-y-2">
        {references.map((r) => (
          <a
            key={r.id}
            href={r.url}
            className="flex items-center gap-3 p-3 bg-card rounded-md shadow-card hover:shadow-card-hover transition-shadow group"
          >
            <div className="h-8 w-8 rounded bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground shrink-0">
              {r.source.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground group-hover:text-brand transition-colors truncate">
                {r.title}
              </p>
              <p className="text-xs text-muted-foreground">{r.source}</p>
            </div>
            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground group-hover:text-brand transition-colors shrink-0" />
          </a>
        ))}
      </div>
    </div>
  );
}
