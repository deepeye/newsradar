import { TrendingCard } from "./trending-card";
import type { PlatformTrendingCard } from "@/lib/types/dashboard";

interface TrendingGridProps {
  cards: PlatformTrendingCard[];
}

export function TrendingGrid({ cards }: TrendingGridProps) {
  return (
    <div className="grid grid-cols-2 gap-md">
      {cards.map((card) => (
        <TrendingCard key={card.platform} card={card} />
      ))}
    </div>
  );
}
