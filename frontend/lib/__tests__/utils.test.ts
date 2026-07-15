import { describe, expect, it } from "vitest";

import { cn } from "@/lib/utils";

describe("cn", () => {
  it("lets a design-system type-scale override (text-h1) win over a base Tailwind font-size class", () => {
    // Regression: without registering the custom design_system.md §7 type
    // scale in tailwind-merge's font-size group, overriding a component's
    // base "text-sm" via className="text-h1" would keep both classes
    // instead of the override replacing it.
    const result = cn("text-sm font-semibold tabular-nums", "text-h1");
    expect(result).toContain("text-h1");
    expect(result).not.toContain("text-sm");
  });

  it("still dedupes plain Tailwind font-size classes normally", () => {
    const result = cn("text-sm", "text-lg");
    expect(result).toBe("text-lg");
  });
});
