import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/risk/api/risk-api", () => ({
  riskApi: {
    getRiskAssessments: vi.fn(),
    getRiskByScan: vi.fn(),
    calculateRiskForScan: vi.fn(),
    getRiskSummary: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { riskApi } from "@/features/risk/api/risk-api";
import { ScanRiskSection } from "@/features/risk/components/scan-risk-section";
import { toast } from "sonner";

const mockedGetRiskByScan = vi.mocked(riskApi.getRiskByScan);
const mockedCalculate = vi.mocked(riskApi.calculateRiskForScan);

describe("ScanRiskSection", () => {
  it("does not offer Calculate Risk for a non-completed scan (frontend restraint, no fabricated eligibility)", async () => {
    mockedGetRiskByScan.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "not found", status: 404 })
    );
    renderWithQueryClient(<ScanRiskSection scanId="scan-1" scanStatus="RUNNING" />);

    await waitFor(() =>
      expect(
        screen.getByText("Risk can be calculated once this scan completes.")
      ).toBeInTheDocument()
    );
    expect(screen.queryByRole("button", { name: /calculate risk/i })).not.toBeInTheDocument();
  });

  it("shows Calculate Risk (not Recalculate) when no risk exists yet for a completed scan", async () => {
    mockedGetRiskByScan.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "not found", status: 404 })
    );
    renderWithQueryClient(<ScanRiskSection scanId="scan-1" scanStatus="COMPLETED" />);

    expect(await screen.findByRole("button", { name: "Calculate Risk" })).toBeInTheDocument();
  });

  it("shows Recalculate Risk once a risk assessment already exists", async () => {
    mockedGetRiskByScan.mockResolvedValue({
      id: "risk-1",
      scope: "SCAN",
      risk_score: 7.2,
      risk_level: "HIGH",
      calculation_version: "1.0.0",
      calculated_at: "2026-07-15T00:00:00Z",
      supporting_factors: {},
      scan_id: "scan-1",
      asset_id: null,
      vulnerability_id: null,
      service_id: null,
    });
    renderWithQueryClient(<ScanRiskSection scanId="scan-1" scanStatus="COMPLETED" />);

    expect(await screen.findByText("7.2")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Recalculate Risk" })
    ).toBeInTheDocument();
  });

  it("prevents duplicate submission while the calculation is pending and never fabricates a score", async () => {
    mockedGetRiskByScan.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "not found", status: 404 })
    );
    let resolveCalc: (value: Awaited<ReturnType<typeof mockedCalculate>>) => void = () => {};
    mockedCalculate.mockImplementation(
      () => new Promise((resolve) => { resolveCalc = resolve; })
    );

    const user = userEvent.setup();
    renderWithQueryClient(<ScanRiskSection scanId="scan-1" scanStatus="COMPLETED" />);

    const button = await screen.findByRole("button", { name: "Calculate Risk" });
    await user.click(button);
    await waitFor(() => expect(screen.getByRole("button")).toBeDisabled());
    await user.click(screen.getByRole("button"));

    expect(mockedCalculate).toHaveBeenCalledTimes(1);
    // No score rendered while pending — nothing fabricated client-side.
    expect(screen.queryByText(/^\d+\.\d$/)).not.toBeInTheDocument();

    resolveCalc({
      id: "risk-1",
      scope: "SCAN",
      risk_score: 7.2,
      risk_level: "HIGH",
      calculation_version: "1.0.0",
      calculated_at: "2026-07-15T00:00:00Z",
      supporting_factors: {},
      scan_id: "scan-1",
      asset_id: null,
      vulnerability_id: null,
      service_id: null,
    });
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith("Risk calculated"));
  });

  it("surfaces a calculation failure safely without blaming AI", async () => {
    mockedGetRiskByScan.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "not found", status: 404 })
    );
    mockedCalculate.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "Scan job with ID scan-1 not found.", status: 404 })
    );
    const user = userEvent.setup();
    renderWithQueryClient(<ScanRiskSection scanId="scan-1" scanStatus="COMPLETED" />);

    await user.click(await screen.findByRole("button", { name: "Calculate Risk" }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Scan job with ID scan-1 not found.")
    );
  });
});
