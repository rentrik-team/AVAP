import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EventMetadata } from "@/features/audit/components/event-metadata";

describe("EventMetadata", () => {
  it("renders humanized keys and plain-text values generically", () => {
    render(
      <EventMetadata
        metadata={{
          risk_score: 8.7,
          risk_level: "CRITICAL",
          calculation_version: "1.0.0",
        }}
      />
    );

    expect(screen.getByText("Risk Score")).toBeInTheDocument();
    expect(screen.getByText("8.7")).toBeInTheDocument();
    expect(screen.getByText("Risk Level")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("renders a one-level-nested object flattened as inert text, not as HTML", () => {
    render(
      <EventMetadata
        metadata={{
          failure_category: "AIProviderException",
          details: { retryable: true, count: 2 },
        }}
      />
    );

    expect(screen.getByText("AIProviderException")).toBeInTheDocument();
    expect(screen.getByText(/Retryable: Yes, Count: 2/)).toBeInTheDocument();
    expect(document.querySelector("script")).toBeNull();
  });

  it("renders HTML-like metadata values as literal text, never interpreted", () => {
    render(
      <EventMetadata metadata={{ note: "<img src=x onerror=alert(1)>" }} />
    );

    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
  });

  it("shows a safe fallback when metadata is empty", () => {
    render(<EventMetadata metadata={{}} />);
    expect(screen.getByText("No additional metadata recorded.")).toBeInTheDocument();
  });
});
