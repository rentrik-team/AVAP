import { describe, expect, it } from "vitest";

import { resolveAuditResourceLink } from "@/features/audit/lib/resource-link";
import type { AuditEventResponse } from "@/features/audit/types/audit";

function event(overrides: Partial<AuditEventResponse>): AuditEventResponse {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    event_type: "SCAN_CREATED",
    category: "SCAN",
    outcome: "SUCCESS",
    actor_type: "ANONYMOUS",
    actor_id: null,
    resource_type: null,
    resource_id: null,
    scan_id: null,
    request_id: null,
    source_ip: null,
    event_metadata: {},
    occurred_at: "2026-07-15T00:00:00Z",
    ...overrides,
  };
}

describe("resolveAuditResourceLink", () => {
  it("links a SCAN resource to the existing scan detail route", () => {
    const link = resolveAuditResourceLink(
      event({ resource_type: "SCAN", resource_id: "scan-1" })
    );
    expect(link).toEqual({ href: "/scans/scan-1", label: "scan-1" });
  });

  it("links a REPORT resource to the existing report detail route", () => {
    const link = resolveAuditResourceLink(
      event({ resource_type: "REPORT", resource_id: "report-1" })
    );
    expect(link).toEqual({ href: "/reports/report-1", label: "report-1" });
  });

  it("never links TARGET, RISK_ASSESSMENT, or AI_RECOMMENDATION — no detail route exists for any of them", () => {
    expect(
      resolveAuditResourceLink(event({ resource_type: "TARGET", resource_id: "target-1" }))
    ).toBeNull();
    expect(
      resolveAuditResourceLink(
        event({ resource_type: "RISK_ASSESSMENT", resource_id: "risk-1" })
      )
    ).toBeNull();
    expect(
      resolveAuditResourceLink(
        event({ resource_type: "AI_RECOMMENDATION", resource_id: "rec-1" })
      )
    ).toBeNull();
  });

  it("returns null when there is no resource_id at all", () => {
    expect(resolveAuditResourceLink(event({ resource_type: "SCAN" }))).toBeNull();
  });
});
