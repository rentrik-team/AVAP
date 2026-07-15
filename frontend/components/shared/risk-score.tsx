import { formatRiskScore } from "@/utils/format";
import { cn } from "@/lib/utils";

/**
 * Purely typographic numeric risk score (0.0–10.0). Deliberately not
 * color-coded by risk level — pair it with <RiskLevelBadge> for the
 * categorical signal instead of conflating the two.
 */
export function RiskScore({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  return (
    <span className={cn("font-mono text-sm font-semibold tabular-nums", className)}>
      {formatRiskScore(score)}
      <span className="ml-0.5 font-sans text-xs font-normal text-muted-foreground">
        /10
      </span>
    </span>
  );
}
