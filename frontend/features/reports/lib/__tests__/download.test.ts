import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { triggerBrowserDownload } from "@/features/reports/lib/download";

describe("triggerBrowserDownload", () => {
  const createObjectURL = vi.fn(() => "blob:mock-url");
  const revokeObjectURL = vi.fn();

  beforeEach(() => {
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = revokeObjectURL;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("saves the blob using the server's own filename convention and cleans up the object URL", () => {
    const blob = new Blob(["%PDF-fake"], { type: "application/pdf" });
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    triggerBrowserDownload(blob, "avap-report-11111111-1111-1111-1111-111111111111.pdf");

    expect(createObjectURL).toHaveBeenCalledWith(blob);
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock-url");

    clickSpy.mockRestore();
  });
});
