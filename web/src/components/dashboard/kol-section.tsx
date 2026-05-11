import { KOLColumn } from "./kol-column";
import type { KOLColumn as KOLColumnType } from "@/lib/types/dashboard";
import { SectionHeader } from "@/components/shared/section-header";
import { Users } from "lucide-react";

interface KOLSectionProps {
  columns: KOLColumnType[];
}

export function KOLSection({ columns }: KOLSectionProps) {
  return (
    <section>
      <SectionHeader
        icon={Users}
        title="KOL 深度洞察"
        subtitle="跨平台意见领袖与热点观点"
        className="mb-4"
      />
      <div className="grid grid-cols-3 gap-md">
        {columns.map((col, i) => (
          <KOLColumn key={`${col.platform}-${i}`} column={col} />
        ))}
      </div>
    </section>
  );
}
