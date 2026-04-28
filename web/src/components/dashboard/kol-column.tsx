import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KOLPost } from "./kol-post";
import type { KOLColumn as KOLColumnType } from "@/lib/types/dashboard";

interface KOLColumnProps {
  column: KOLColumnType;
}

export function KOLColumn({ column }: KOLColumnProps) {
  return (
    <Card className="bg-card shadow-card hover:shadow-card-hover transition-shadow border-0">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-foreground">
          {column.platformLabel}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="divide-y divide-outline-variant/20">
          {column.posts.map((post) => (
            <KOLPost key={post.id} post={post} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
