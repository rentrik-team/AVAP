import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// `globals: false` in vitest.config.ts means RTL can't auto-detect a
// global `afterEach` to hook its own cleanup into, so unmount explicitly —
// otherwise DOM from earlier tests in the same file lingers and later
// getByText/queryByText assertions can match stale nodes. Mock call
// counts are cleared too, so each test's toHaveBeenCalledTimes reflects
// only that test, not every test that ran before it in the same file.
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// next-themes/Recharts touch matchMedia and ResizeObserver, neither of
// which jsdom implements.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = window.ResizeObserver ?? MockResizeObserver;

if (!navigator.clipboard) {
  Object.assign(navigator, {
    clipboard: { writeText: async () => {} },
  });
}
