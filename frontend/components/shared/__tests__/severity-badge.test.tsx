import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SeverityBadge } from "@/components/shared/severity-badge";

describe("SeverityBadge", () => {
  it("always renders a text label alongside color — never a color-only indicator", () => {
    render(<SeverityBadge severity="critical" />);
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("renders the Unknown label for the unknown severity bucket rather than hiding it", () => {
    render(<SeverityBadge severity="unknown" />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});
