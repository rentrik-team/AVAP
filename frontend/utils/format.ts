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
