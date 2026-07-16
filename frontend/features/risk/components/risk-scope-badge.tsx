import { Badge } from "@/components/ui/badge";
import type { RiskScope } from "@/features/risk/types/risk";

/**
 * Scope is a domain category, not a security severity/status — deliberately
 * NOT SeverityBadge or ScanStatusBadge (those own different semantics).
 */
const SCOPE_LABELS: Record<RiskScope, string> = {
  VULNERABILITY: "Vulnerability",
  ASSET: "Asset",
  SCAN: "Scan",
  ASSESSMENT: "Assessment",
};

export function RiskScopeBadge({
  scope,
  className,
}: {
  scope: RiskScope;
  className?: string;
}) {
  return (
    <Badge variant="outline" className={className}>
      {SCOPE_LABELS[scope]}
    </Badge>
  );
}
