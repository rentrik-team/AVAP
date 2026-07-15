import { describe, expect, it } from "vitest";

import {
  formatCount,
  formatDuration,
  formatPercent,
  formatRiskScore,
} from "@/utils/format";

describe("formatRiskScore", () => {
  it("always shows one decimal place across the 0.0-10.0 scale", () => {
    expect(formatRiskScore(0)).toBe("0.0");
    expect(formatRiskScore(9.5)).toBe("9.5");
    expect(formatRiskScore(10)).toBe("10.0");
  });
});

describe("formatPercent", () => {
  it("formats with one decimal by default", () => {
    expect(formatPercent(66.666)).toBe("66.7%");
  });

  it("formats a zero-denominator empty state as 0.0%, never NaN", () => {
    expect(formatPercent(0)).toBe("0.0%");
  });
});

describe("formatCount", () => {
  it("groups large counts with locale separators", () => {
    expect(formatCount(1234)).toBe("1,234");
  });

  it("renders zero plainly (a valid empty-database state)", () => {
    expect(formatCount(0)).toBe("0");
  });
});

describe("formatDuration", () => {
  it("renders an em dash for a still-running scan with no duration yet, never a fabricated value", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(undefined)).toBe("—");
  });

  it("renders sub-minute durations in seconds", () => {
    expect(formatDuration(45)).toBe("45s");
  });

  it("renders sub-hour durations in minutes and seconds", () => {
    expect(formatDuration(150)).toBe("2m 30s");
  });

  it("renders hour-scale durations in hours and minutes", () => {
    expect(formatDuration(3725)).toBe("1h 2m");
  });
});
