import type { RiskScope, RiskSupportingFactors } from "@/features/risk/types/risk";

/**
 * Strict allowlisted presentation of supporting_factors (raw backend
 * JSONB). Only known keys — verified against app/risk_engine/calculator.py
 * (VULNERABILITY) and aggregator.py (ASSET/SCAN/ASSESSMENT) — are ever
 * read or rendered. Any other key present in the payload is silently
 * omitted from this view: never executed, never used as a class name or
 * HTML, never recursed into. This is a deliberate omit-unknown-keys
 * choice (vs. an inert key/value dump) to keep the premium view free of
 * internal engine noise that isn't part of the documented contract.
 */
const VULNERABILITY_FACTOR_LABELS: Record<string, string> = {
  base_score: "Base score",
  cvss_used: "CVSS used",
  severity_rating: "Scanner severity",
  affected_asset_count: "Affected assets",
  affected_service_count: "Affected services",
  asset_influence_bonus: "Asset influence bonus",
  service_influence_bonus: "Service influence bonus",
};

const AGGREGATION_FACTOR_LABELS: Record<string, string> = {
  aggregation_method: "Aggregation method",
  contributing_count: "Contributing components",
  contributing_entity_id: "Contributing entity",
};

function formatFactorValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  return String(value);
}

export function SupportingFactors({
  scope,
  factors,
}: {
  scope: RiskScope;
  factors: RiskSupportingFactors;
}) {
  const labels =
    scope === "VULNERABILITY" ? VULNERABILITY_FACTOR_LABELS : AGGREGATION_FACTOR_LABELS;

  const entries = Object.entries(labels)
    .filter(([key]) => key in factors)
    .map(([key, label]) => [label, formatFactorValue(factors[key])] as const);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No supporting factors recorded.</p>;
  }

  return (
    <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {entries.map(([label, value]) => (
        <div key={label} className="flex flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">{label}</dt>
          <dd className="font-mono text-sm break-words tabular-nums text-foreground">
            {value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
