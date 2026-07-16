import { format, formatDistanceToNow } from "date-fns";

const numberFormatter = new Intl.NumberFormat("en-US");

export function formatCount(value: number): string {
  return numberFormatter.format(value);
}

/** Risk scores are always 0.0–10.0 per the Risk Engine contract. */
export function formatRiskScore(value: number): string {
  return value.toFixed(1);
}

export function formatPercent(value: number, fractionDigits = 1): string {
  return `${value.toFixed(fractionDigits)}%`;
}

export function formatDateTime(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return format(date, "MMM d, yyyy 'at' HH:mm");
}

export function formatRelativeTime(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return formatDistanceToNow(date, { addSuffix: true });
}

/** Capitalizes a free-text backend value (e.g. scan_type "full" -> "Full")
 * for display without inventing a fixed label map for an open-ended field. */
export function formatLabel(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

/**
 * Humanizes a snake_case or SCREAMING_SNAKE_CASE backend value (event
 * types, categories, resource/actor types, and audit metadata keys) into a
 * readable label, e.g. "RISK_CALCULATION_COMPLETED" -> "Risk Calculation
 * Completed", "risk_score" -> "Risk Score". Generic by design rather than
 * a per-value label map — there are 15+ event type values alone (plus an
 * open-ended set of metadata keys), and the raw values are already
 * self-descriptive words. Case-insensitive on the input so it works
 * equally for enum values (uppercase) and metadata keys (lowercase).
 */
export function formatEnumLabel(value: string): string {
  return value
    .split("_")
    .map((word) =>
      word.toUpperCase() === "AI" ? "AI" : word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    )
    .join(" ");
}

/** Formats a byte count as a human-readable size (report file sizes). */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

/** Whole-second scan/report execution durations into a compact "1h 5m" form. */
export function formatDuration(totalSeconds: number | null | undefined): string {
  if (totalSeconds === null || totalSeconds === undefined) {
    return "—";
  }

  const seconds = Math.round(totalSeconds);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  return `${remainingSeconds}s`;
}
