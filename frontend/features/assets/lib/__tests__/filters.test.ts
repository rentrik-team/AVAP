import { describe, expect, it } from "vitest";

import { isInvalidPortFilter, parsePortFilter } from "@/features/assets/lib/filters";

describe("parsePortFilter", () => {
  it("parses a valid port", () => {
    expect(parsePortFilter("443")).toBe(443);
    expect(parsePortFilter(" 22 ")).toBe(22);
  });

  it("returns undefined for empty input", () => {
    expect(parsePortFilter("")).toBeUndefined();
    expect(parsePortFilter("   ")).toBeUndefined();
  });

  it("never coerces non-numeric text into a number", () => {
    expect(parsePortFilter("abc")).toBeUndefined();
    expect(parsePortFilter("443abc")).toBeUndefined();
    expect(parsePortFilter("44.3")).toBeUndefined();
    expect(parsePortFilter("-1")).toBeUndefined();
  });

  it("rejects out-of-range ports (backend constraint: 1-65535)", () => {
    expect(parsePortFilter("0")).toBeUndefined();
    expect(parsePortFilter("65536")).toBeUndefined();
    expect(parsePortFilter("65535")).toBe(65535);
    expect(parsePortFilter("1")).toBe(1);
  });
});

describe("isInvalidPortFilter", () => {
  it("is false for empty input (no filter applied, not an error)", () => {
    expect(isInvalidPortFilter("")).toBe(false);
  });

  it("is true only for non-empty, unparseable input", () => {
    expect(isInvalidPortFilter("abc")).toBe(true);
    expect(isInvalidPortFilter("443")).toBe(false);
  });
});
