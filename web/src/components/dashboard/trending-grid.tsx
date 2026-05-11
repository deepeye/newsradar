import { TrendingCard } from "./trending-card";
import type { PlatformTrendingCard } from "@/lib/types/dashboard";

interface TrendingGridProps {
  cards: PlatformTrendingCard[];
}

export function TrendingGrid({ cards }: TrendingGridProps) {
  return (
    <div className="grid grid-cols-2 gap-md">
      {cards.map((card, i) => (
        <TrendingCard key={`${card.platform}-${i}`} card={card} />
      ))}
    </div>
  );
}
