/**
 * Immutable security severity / risk-level color semantics, shared by
 * SeverityBadge and RiskBadge. RiskLevel (app.core.enums.RiskLevel) and
 * Vulnerability.severity_rating are two distinct backend taxonomies (see
 * modules_docs/09_dashboard.md §"Dashboard Walkthrough") but both use the
 * same five-value scale, so both render through this one palette. Purple
 * (the brand accent) must never appear here (design_system.md §2.3).
 *
 * Token values live in app/globals.css and mirror design_system.md §5
 * exactly (foreground/background/border per severity).
 */

export type SeverityKey =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational"
  | "unknown";

export const SEVERITY_ORDER: SeverityKey[] = [
  "critical",
  "high",
  "medium",
  "low",
  "informational",
  "unknown",
];

interface SeverityMeta {
  label: string;
  /** Tailwind text-color utility (maps to the --severity-* CSS variable). */
  textClass: string;
  /** Tailwind soft background utility for badges. */
  bgClass: string;
  /** Tailwind border-color utility (design_system.md §21 badge recipe). */
  borderClass: string;
  /** Raw `var(--severity-*)` reference for Recharts fill/stroke props. */
  chartColor: string;
}

export const SEVERITY_META: Record<SeverityKey, SeverityMeta> = {
  critical: {
    label: "Critical",
    textClass: "text-severity-critical",
    bgClass: "bg-severity-critical-bg",
    borderClass: "border-severity-critical-border",
    chartColor: "var(--severity-critical)",
  },
  high: {
    label: "High",
    textClass: "text-severity-high",
    bgClass: "bg-severity-high-bg",
    borderClass: "border-severity-high-border",
    chartColor: "var(--severity-high)",
  },
  medium: {
    label: "Medium",
    textClass: "text-severity-medium",
    bgClass: "bg-severity-medium-bg",
    borderClass: "border-severity-medium-border",
    chartColor: "var(--severity-medium)",
  },
  low: {
    label: "Low",
    textClass: "text-severity-low",
    bgClass: "bg-severity-low-bg",
    borderClass: "border-severity-low-border",
    chartColor: "var(--severity-low)",
  },
  informational: {
    label: "Informational",
    textClass: "text-severity-informational",
    bgClass: "bg-severity-informational-bg",
    borderClass: "border-severity-informational-border",
    chartColor: "var(--severity-informational)",
  },
  unknown: {
    label: "Unknown",
    textClass: "text-severity-unknown",
    bgClass: "bg-severity-unknown-bg",
    borderClass: "border-severity-unknown-border",
    chartColor: "var(--severity-unknown)",
  },
};

/** Normalizes a RiskLevel enum value ("CRITICAL"|"HIGH"|...) to a SeverityKey. */
export function riskLevelToSeverityKey(riskLevel: string): SeverityKey {
  const normalized = riskLevel.toLowerCase();
  if (
    normalized === "critical" ||
    normalized === "high" ||
    normalized === "medium" ||
    normalized === "low" ||
    normalized === "informational"
  ) {
    return normalized;
  }
  return "unknown";
}

/**
 * Normalizes a raw Vulnerability.severity_rating string (e.g. "Critical",
 * "None") to a SeverityKey, mirroring the backend's own bucketing rule:
 * "None" is informational; anything else unrecognized is "unknown".
 */
export function severityRatingToKey(severityRating: string): SeverityKey {
  const normalized = severityRating.toLowerCase();
  if (normalized === "none") return "informational";
  if (
    normalized === "critical" ||
    normalized === "high" ||
    normalized === "medium" ||
    normalized === "low"
  ) {
    return normalized;
  }
  return "unknown";
}
