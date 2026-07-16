import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SupportingFactors } from "@/features/risk/components/supporting-factors";

describe("SupportingFactors", () => {
  it("renders the exact VULNERABILITY-scope allowlisted keys with humanized labels", () => {
    render(
      <SupportingFactors
        scope="VULNERABILITY"
        factors={{
          base_score: 8.3,
          cvss_used: false,
          severity_rating: "High",
          affected_asset_count: 3,
          affected_service_count: 2,
          asset_influence_bonus: 0.2,
          service_influence_bonus: 0.05,
        }}
      />
    );

    expect(screen.getByText("Base score")).toBeInTheDocument();
    // Non-integer values render with two-decimal precision.
    expect(screen.getByText("8.30")).toBeInTheDocument();
    expect(screen.getByText("CVSS used")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.getByText("Affected assets")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders the exact aggregation-scope allowlisted keys (ASSET/SCAN/ASSESSMENT)", () => {
    render(
      <SupportingFactors
        scope="SCAN"
        factors={{
          aggregation_method: "maximum",
          contributing_count: 4,
          contributing_entity_id: "22222222-2222-2222-2222-222222222222",
        }}
      />
    );

    expect(screen.getByText("Aggregation method")).toBeInTheDocument();
    expect(screen.getByText("maximum")).toBeInTheDocument();
    expect(screen.getByText("Contributing components")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("Contributing entity")).toBeInTheDocument();
  });

  it("never crashes on an unrecognized key, and never renders it", () => {
    const factors: Record<string, unknown> = {
      base_score: 5.0,
      internal_debug_flag: true,
      unexpected_future_key: { nested: "object" },
    };
    // Set via bracket notation (not an object-literal `__proto__` key,
    // which would set the prototype instead of an own property) to prove
    // an unexpected key is genuinely ignored, not just absent.
    factors["api_secret"] = "should-never-render";

    render(<SupportingFactors scope="VULNERABILITY" factors={factors} />);

    expect(screen.getByText("Base score")).toBeInTheDocument();
    expect(screen.queryByText(/internal_debug_flag/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/unexpected_future_key/i)).not.toBeInTheDocument();
    expect(screen.queryByText("should-never-render")).not.toBeInTheDocument();
  });

  it("renders a null contributing_entity_id (empty-contributions aggregation) as an em dash, not a crash", () => {
    render(
      <SupportingFactors
        scope="ASSESSMENT"
        factors={{
          aggregation_method: "maximum",
          contributing_count: 0,
          contributing_entity_id: null,
        }}
      />
    );

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("shows a safe fallback message when no allowlisted keys are present", () => {
    render(<SupportingFactors scope="VULNERABILITY" factors={{}} />);
    expect(screen.getByText("No supporting factors recorded.")).toBeInTheDocument();
  });
});
