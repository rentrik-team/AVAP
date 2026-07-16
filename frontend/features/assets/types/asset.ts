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
  assets: AssetResponse[];
  total: number;
}

/** Maps 1:1 to GET /assets query parameters (app/api/routes/v1/assets.py).
 * `ip` is an exact match server-side; `hostname`/`cve` are case-insensitive
 * substrings; `port` is exact. */
export interface AssetListFilters {
  ip?: string;
  hostname?: string;
  port?: number;
  cve?: string;
}
