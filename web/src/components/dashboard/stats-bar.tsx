interface StatsBarProps {
  activeThreads: number;
  topicAlerts: number;
}

function formatStat(n: number): string {
  if (n >= 1000) return `${Math.round(n / 1000)}k+`;
  return String(n);
}

export function StatsBar({ activeThreads, topicAlerts }: StatsBarProps) {
  return (
    <div className="flex items-center gap-8 py-3 px-lg bg-card rounded-md shadow-card">
      <div className="flex items-center gap-2">
        <span className="font-serif text-lg font-bold text-brand">
          {formatStat(activeThreads)}
        </span>
        <span className="text-sm text-muted-foreground">ACTIVE THREADS</span>
      </div>
      <div className="w-px h-6 bg-outline-variant/30" />
      <div className="flex items-center gap-2">
        <span className="font-serif text-lg font-bold text-tertiary">
          {topicAlerts}
        </span>
        <span className="text-sm text-muted-foreground">TOPIC ALERTS</span>
      </div>
    </div>
  );
}
