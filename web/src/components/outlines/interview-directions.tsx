import { Mic } from "lucide-react";
import type { InterviewDirection } from "@/lib/types/outlines";

interface InterviewDirectionsProps {
  directions: InterviewDirection[];
}

export function InterviewDirections({ directions }: InterviewDirectionsProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Mic className="h-4 w-4 text-brand" />
        <h3 className="font-serif text-base font-semibold">延伸采访方向</h3>
      </div>
      <div className="space-y-2">
        {directions.map((d, i) => (
          <div
            key={d.id ?? `dir-${i}`}
            className="flex items-start gap-3 p-3 bg-card rounded-md shadow-card"
          >
            <span className="flex items-center justify-center h-6 w-6 rounded-full bg-tertiary/10 text-tertiary text-xs font-bold shrink-0">
              {i + 1}
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">
                {d.role}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {d.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
