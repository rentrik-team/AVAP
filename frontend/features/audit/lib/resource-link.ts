import type { AuditEventResponse } from "@/features/audit/types/audit";

export interface AuditResourceLink {
  href: string;
  label: string;
}

/**
 * Resolves a navigable link only for resource types that actually have an
 * existing detail route (Scan, Report). Target/RiskAssessment/AIRecommendation
 * have no detail route in this frontend (Target has no detail page at all;
 * Risk/AI have no get-by-id route) — those render as plain, unlinked text
 * rather than dead navigation.
 */
export function resolveAuditResourceLink(
  event: AuditEventResponse
): AuditResourceLink | null {
  if (!event.resource_id) return null;
  switch (event.resource_type) {
    case "SCAN":
      return { href: `/scans/${event.resource_id}`, label: event.resource_id };
    case "REPORT":
      return { href: `/reports/${event.resource_id}`, label: event.resource_id };
    default:
      return null;
  }
}
