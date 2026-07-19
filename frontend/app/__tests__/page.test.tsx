import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/dashboard/api/dashboard-api", () => ({
  dashboardApi: {
    getSummary: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_targets: 1,
      total_scans: 1,
      total_assets: 1,
      unique_vulnerability_count: 1,
      critical_vulnerability_count: 1,
      total_reports_generated: 0,
      overall_risk_score: 9.1,
      overall_risk_level: "CRITICAL",
      high_risk_asset_count: 1,
    }),
    getAssetStatistics: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_assets: 1,
      total_network_services: 2,
      recently_discovered_assets: [],
    }),
    getVulnerabilityStatistics: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      unique_vulnerability_count: 1,
      finding_count: 1,
      severity_distribution: {
        critical: 1,
        high: 0,
        medium: 0,
        low: 0,
        informational: 0,
        unknown: 0,
      },
    }),
    getRiskStatistics: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      overall_risk_score: 9.1,
      overall_risk_level: "CRITICAL",
      risk_level_distribution: {
        critical: 1,
        high: 0,
        medium: 0,
        low: 0,
        informational: 0,
      },
      top_risk_assets: [
        {
          asset_id: "a1",
          ipv4: "10.0.0.9",
          hostname: null,
          risk_score: 9.1,
          risk_level: "CRITICAL",
        },
      ],
      top_risk_vulnerabilities: [],
    }),
    getScanStatistics: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_scans: 1,
      scans_by_status: {
        pending: 0,
        running: 0,
        completed: 1,
        failed: 0,
        cancelled: 0,
      },
      scan_success_rate_percent: 100,
      average_scan_duration_seconds: 42,
      recent_scans: [],
    }),
    getReportStatistics: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_reports_generated: 0,
      reports_by_format: {},
      latest_report_generated_at: null,
      recent_reports: [],
    }),
    getAIStatistics: vi.fn().mockResolvedValue({
      generated_at: "2026-07-15T00:00:00Z",
      total_recommendations: 0,
      recommendations_by_provider: {},
      recommendations_by_model: {},
      recommendations_by_severity: {},
      eligible_vulnerability_risk_count: 1,
      current_recommendation_count: 0,
      missing_recommendation_count: 1,
      remediation_coverage_percent: 0,
    }),
  },
}));

import DashboardPage from "@/app/page";

describe("DashboardPage composition", () => {
  it("labels AI coverage as availability, never as effectiveness/accuracy/success rate", async () => {
    renderWithQueryClient(<DashboardPage />);

    await waitFor(() =>
      expect(screen.getByText("AI Remediation Coverage")).toBeInTheDocument()
    );

    expect(screen.queryByText(/AI Effectiveness/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/AI Accuracy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/AI Success Rate/i)).not.toBeInTheDocument();
  });

  it("renders risk score and risk level as two distinct elements for a ranked asset", async () => {
    renderWithQueryClient(<DashboardPage />);

    await waitFor(() => expect(screen.getByText("10.0.0.9")).toBeInTheDocument());

    // "9.1" (numeric score) and "Critical" (categorical level) must be two
    // separate pieces of markup, not a single conflated string.
    const scoreEls = screen.getAllByText("9.1");
    expect(scoreEls.length).toBeGreaterThan(0);
    const levelEls = screen.getAllByText("Critical");
    expect(levelEls.length).toBeGreaterThan(0);
  });
});
