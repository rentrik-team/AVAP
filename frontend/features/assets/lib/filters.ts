/**
 * Parses the Asset list's raw port filter input. Never coerces invalid
 * text into a number sent to the backend — an unparseable or out-of-range
 * value is simply omitted from the request (see ServiceResponse.port,
 * constrained 1-65535 in backend/app/schemas/asset.py).
 */
export function parsePortFilter(raw: string): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  if (!/^\d+$/.test(trimmed)) return undefined;

  const parsed = Number(trimmed);
  if (parsed < 1 || parsed > 65535) return undefined;
  return parsed;
}

/** True only when the user has typed something that failed to parse — used
 * to show an inline validation message rather than silently ignoring input. */
export function isInvalidPortFilter(raw: string): boolean {
  return raw.trim() !== "" && parsePortFilter(raw) === undefined;
}
