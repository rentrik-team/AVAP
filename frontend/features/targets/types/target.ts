/**
 * Mirrors backend/app/schemas/target.py exactly (field names, casing,
 * nullability). Wire-contract types, not UI view models.
 */

export type TargetType = "IPV4" | "CIDR" | "HOSTNAME";

export interface TargetResponse {
  id: string;
  target: string;
  target_type: TargetType;
  created_at: string;
  updated_at: string;
}

export interface TargetListResponse {
  targets: TargetResponse[];
  total: number;
}

export interface CreateTargetRequest {
  target: string;
}

/** Humanized presentation labels only — the stored/API value stays exact. */
export const TARGET_TYPE_LABELS: Record<TargetType, string> = {
  IPV4: "IPv4",
  CIDR: "CIDR",
  HOSTNAME: "Hostname",
};
