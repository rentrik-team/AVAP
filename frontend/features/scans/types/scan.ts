/**
 * Mirrors backend/app/schemas/scan.py exactly (field names, casing,
 * nullability). Wire-contract types, not UI view models.
 */

export type ScanStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface ScanResponse {
  scan_id: string;
  target_id: string;
  status: ScanStatus;
  scan_type: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  execution_duration: number | null;
  failure_reason: string | null;
}

export interface ScanListResponse {
  scans: ScanResponse[];
  total: number;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: ScanStatus;
  updated_at: string;
}

export interface CreateScanRequest {
  target_id: string;
}
