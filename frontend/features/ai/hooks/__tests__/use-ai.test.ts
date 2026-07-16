import { describe, expect, it } from "vitest";

import { isRecommendationFresh } from "@/features/ai/hooks/use-ai";

describe("isRecommendationFresh", () => {
  it("is fresh when generated at or after the risk assessment's calculated_at (exact Module 07 rule)", () => {
    expect(
      isRecommendationFresh("2026-07-15T10:00:00Z", "2026-07-15T09:00:00Z")
    ).toBe(true);
    expect(
      isRecommendationFresh("2026-07-15T09:00:00Z", "2026-07-15T09:00:00Z")
    ).toBe(true);
  });

  it("is stale when the risk assessment was recalculated after generation", () => {
    expect(
      isRecommendationFresh("2026-07-15T08:00:00Z", "2026-07-15T09:00:00Z")
    ).toBe(false);
  });

  it("compares instants, not lexicographic strings (differing ISO precision)", () => {
    expect(
      isRecommendationFresh("2026-07-15T09:00:00.500000Z", "2026-07-15T09:00:00Z")
    ).toBe(true);
  });
});
