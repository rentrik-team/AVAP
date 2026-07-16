/**
 * Mirrors backend/app/schemas/audit.py and app/core/enums.py exactly
 * (field names, casing, exact enum member lists). Wire-contract types,
 * not UI view models.
 *
 * Audit events are a strictly read-only, immutable resource — there is no
 * create/update/delete request schema because none of those endpoints
 * exist (POST/PUT/PATCH/DELETE on /audit return 405 on the backend).
 */

export type AuditEventType =
  | "TARGET_CREATED"
  | "TARGET_UPDATED"
  | "TARGET_DELETED"
  | "SCAN_CREATED"
  | "SCAN_DELETED"
  | "INVENTORY_PROCESSED"
  | "INVENTORY_PROCESSING_FAILED"
  | "RISK_CALCULATION_COMPLETED"
  | "RISK_CALCULATION_FAILED"
  | "AI_RECOMMENDATION_GENERATED"
  | "AI_RECOMMENDATION_FAILED"
  | "REPORT_GENERATED"
  | "REPORT_GENERATION_FAILED"
  | "REPORT_DOWNLOADED"
  | "REPORT_DELETED";

export type AuditEventCategory =
  | "SYSTEM"
  | "TARGET"
  | "SCAN"
  | "INVENTORY"
  | "RISK"
  | "AI"
  | "REPORT";

export type AuditOutcome = "SUCCESS" | "FAILURE";

export type AuditActorType = "SYSTEM" | "ANONYMOUS";

export type AuditResourceType =
  | "TARGET"
  | "SCAN"
  | "RISK_ASSESSMENT"
  | "AI_RECOMMENDATION"
  | "REPORT";

export interface AuditEventResponse {
  id: string;
  event_type: AuditEventType;
  category: AuditEventCategory;
  outcome: AuditOutcome;
  actor_type: AuditActorType;
  actor_id: string | null;
  resource_type: AuditResourceType | null;
  resource_id: string | null;
  scan_id: string | null;
  request_id: string | null;
  source_ip: string | null;
  /**
   * Already validated server-side before persistence (max depth 2, max 20
   * keys/level, str/int/float/bool/None/shallow-dict values only, forbidden
   * secret-key names rejected — app/audit/metadata_policy.py) — a
   * materially stronger guarantee than Risk's raw supporting_factors. Still
   * rendered as plain text only, never as HTML/class names.
   */
  event_metadata: Record<string, unknown>;
  occurred_at: string;
}

export interface AuditEventListResponse {
  events: AuditEventResponse[];
  total: number;
}

/** Maps 1:1 to GET /audit query parameters (app/api/routes/v1/audit.py).
 * occurred_after/occurred_before and resource_id are intentionally not
 * exposed as UI filter inputs in this phase — see AuditFilterBar. */
export interface AuditEventListFilters {
  event_type?: AuditEventType;
  category?: AuditEventCategory;
  outcome?: AuditOutcome;
  resource_type?: AuditResourceType;
  actor_type?: AuditActorType;
  scan_id?: string;
}
