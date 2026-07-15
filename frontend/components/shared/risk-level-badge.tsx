import { SeverityBadge } from "@/components/shared/severity-badge";
import { riskLevelToSeverityKey } from "@/constants/severity";
import type { RiskLevel } from "@/features/dashboard/types/dashboard";

/**
 * Renders a deterministic Module 06 RiskLevel. Visually identical palette
 * to SeverityBadge (both share the same five-value taxonomy) but kept as
 * its own component since RiskLevel and severity_rating are distinct
 * backend concepts that should never be silently interchanged by callers.
 */
export function RiskLevelBadge({
  level,
  className,
}: {
  level: RiskLevel;
  className?: string;
}) {
  return <SeverityBadge severity={riskLevelToSeverityKey(level)} className={className} />;
}
