/**
 * Mirrors backend/app/schemas/asset.py exactly (field names, casing,
 * nullability). Wire-contract types, not UI view models. Assets are
 * scanner-discovered inventory (written only by InventoryService's
 * assessment-package pipeline) — there is no create/update endpoint, only
 * list/detail/delete.
 */

export interface ServiceResponse {
  id: string;
  port: number;
  protocol: string;
  service_name: string;
  product: string | null;
  version: string | null;
  extra_info: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetResponse {
  id: string;
  ipv4: string;
  hostname: string | null;
  operating_system: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetDetailResponse extends AssetResponse {
  services: ServiceResponse[];
}

export interface AssetListResponse {
  assets: AssetDetailResponse[];
  total: number;
}

/** Maps 1:1 to GET /assets query parameters (app/api/routes/v1/assets.py).
 * `ip` is an exact match server-side; `hostname`/`cve` are case-insensitive
 * substrings; `port` is exact. `target_id` scopes to assets discovered via
 * scans of that target (Asset has no direct target_id — the backend joins
 * through scan_findings/scan_jobs). `scan_id` scopes to assets discovered by
 * one specific scan (a direct scan_findings.scan_id match). */
export interface AssetListFilters {
  ip?: string;
  hostname?: string;
  port?: number;
  cve?: string;
  target_id?: string;
  scan_id?: string;
}
