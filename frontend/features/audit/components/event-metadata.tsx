/**
 * Generic (not allowlisted) key/value renderer for event_metadata. This is
 * safe to do here — unlike Risk's supporting_factors — because
 * app/audit/metadata_policy.py already validates every metadata dict
 * server-side *before persistence*: max depth 2, max 20 keys/level, only
 * str/int/float/bool/None/one-level-nested-dict values, and a
 * case-insensitive forbidden-key blocklist (password, token, api_key,
 * secret, authorization, etc.). By the time this ever reaches the browser,
 * it has already passed that gate. Still rendered as plain text only —
 * never HTML, never a class name, never executed.
 */
import { formatEnumLabel } from "@/utils/format";

function formatMetadataValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "object" && !Array.isArray(value)) {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, nested]) => `${formatEnumLabel(key)}: ${formatMetadataValue(nested)}`)
      .join(", ");
  }
  // Defensive fallback for a shape the policy shouldn't allow (e.g. an
  // array) — still just inert text, never interpreted.
  return JSON.stringify(value);
}

export function EventMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const entries = Object.entries(metadata);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No additional metadata recorded.</p>;
  }

  return (
    <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key} className="flex flex-col gap-0.5">
          <dt className="text-xs text-muted-foreground">{formatEnumLabel(key)}</dt>
          <dd className="font-mono text-sm break-words text-foreground">
            {formatMetadataValue(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
