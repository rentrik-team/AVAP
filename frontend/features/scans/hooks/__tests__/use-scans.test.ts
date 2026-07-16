import { describe, expect, it } from "vitest";

import {
  isTerminalScanStatus,
  resolveScanListPollInterval,
  resolveScanStatusPollInterval,
  SCAN_STATUS_POLL_INTERVAL_MS,
} from "@/features/scans/hooks/use-scans";
import type { ScanResponse } from "@/features/scans/types/scan";

function scan(overrides: Partial<ScanResponse> = {}): ScanResponse {
  return {
    scan_id: "11111111-1111-1111-1111-111111111111",
    target_id: "22222222-2222-2222-2222-222222222222",
    status: "PENDING",
    scan_type: "full",
    created_at: "2026-07-15T00:00:00Z",
    updated_at: "2026-07-15T00:00:00Z",
    started_at: null,
    completed_at: null,
    execution_duration: null,
    failure_reason: null,
    ...overrides,
  };
}

describe("isTerminalScanStatus", () => {
  it("treats only COMPLETED and FAILED as terminal", () => {
    expect(isTerminalScanStatus("COMPLETED")).toBe(true);
    expect(isTerminalScanStatus("FAILED")).toBe(true);
    expect(isTerminalScanStatus("PENDING")).toBe(false);
    expect(isTerminalScanStatus("RUNNING")).toBe(false);
  });
});

describe("resolveScanStatusPollInterval", () => {
  it("polls at the bounded interval while PENDING or RUNNING", () => {
    expect(resolveScanStatusPollInterval("PENDING")).toBe(SCAN_STATUS_POLL_INTERVAL_MS);
    expect(resolveScanStatusPollInterval("RUNNING")).toBe(SCAN_STATUS_POLL_INTERVAL_MS);
  });

  it("stops polling once the scan reaches a terminal state", () => {
    expect(resolveScanStatusPollInterval("COMPLETED")).toBe(false);
    expect(resolveScanStatusPollInterval("FAILED")).toBe(false);
  });

  it("does not poll before any status is known", () => {
    expect(resolveScanStatusPollInterval(undefined)).toBe(false);
  });
});

describe("resolveScanListPollInterval", () => {
  it("polls while at least one scan in the page is active", () => {
    const scans = [scan({ status: "COMPLETED" }), scan({ status: "RUNNING" })];
    expect(resolveScanListPollInterval(scans)).toBe(SCAN_STATUS_POLL_INTERVAL_MS);
  });

  it("stops once every scan in the page is terminal", () => {
    const scans = [scan({ status: "COMPLETED" }), scan({ status: "FAILED" })];
    expect(resolveScanListPollInterval(scans)).toBe(false);
  });

  it("does not poll an empty or not-yet-loaded page", () => {
    expect(resolveScanListPollInterval([])).toBe(false);
    expect(resolveScanListPollInterval(undefined)).toBe(false);
  });
});
