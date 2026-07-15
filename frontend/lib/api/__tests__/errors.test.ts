import { describe, expect, it } from "vitest";

import { ApiError, normalizeApiError } from "@/lib/api/errors";

function fakeAxiosError(overrides: Record<string, unknown>) {
  return { isAxiosError: true, ...overrides };
}

describe("normalizeApiError", () => {
  it("extracts code/message/details from the backend's standardized ErrorResponse envelope", () => {
    const error = fakeAxiosError({
      response: {
        status: 404,
        data: {
          success: false,
          data: null,
          error: { code: "NOT_FOUND", message: "Target not found", details: { id: "x" } },
        },
      },
    });

    const result = normalizeApiError(error);

    expect(result).toBeInstanceOf(ApiError);
    expect(result.code).toBe("NOT_FOUND");
    expect(result.message).toBe("Target not found");
    expect(result.status).toBe(404);
    expect(result.details).toEqual({ id: "x" });
  });

  it("never leaks the raw backend message when the response body isn't the expected envelope", () => {
    const error = fakeAxiosError({
      response: { status: 500, data: "<html>Internal Server Error</html>" },
    });

    const result = normalizeApiError(error);

    expect(result.code).toBe("UNEXPECTED_RESPONSE");
    expect(result.message).not.toContain("<html>");
  });

  it("maps a request timeout to a stable, user-safe code", () => {
    const error = fakeAxiosError({ code: "ECONNABORTED" });

    const result = normalizeApiError(error);

    expect(result.code).toBe("REQUEST_TIMEOUT");
    expect(result.status).toBeNull();
  });

  it("maps a network failure (no response at all) to NETWORK_ERROR", () => {
    const error = fakeAxiosError({ response: undefined });

    const result = normalizeApiError(error);

    expect(result.code).toBe("NETWORK_ERROR");
    expect(result.status).toBeNull();
  });

  it("normalizes a completely unknown thrown value without leaking it", () => {
    const result = normalizeApiError(new Error("some internal stack trace detail"));

    expect(result.code).toBe("UNKNOWN_ERROR");
    expect(result.message).not.toContain("stack trace");
  });
});
