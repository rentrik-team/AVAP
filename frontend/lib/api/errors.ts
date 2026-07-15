import axios from "axios";

import type { ApiErrorEnvelope } from "@/types/api";

/**
 * Normalized, user-safe representation of an API failure. Every service
 * function throws this instead of a raw AxiosError, so components never
 * see stack traces, HTTP internals, or backend implementation details —
 * only a stable `code` (switch on this) and a human-readable `message`.
 */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly details: Record<string, unknown> | null;

  constructor(params: {
    code: string;
    message: string;
    status: number | null;
    details?: Record<string, unknown> | null;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.code = params.code;
    this.status = params.status;
    this.details = params.details ?? null;
  }
}

function isErrorEnvelope(data: unknown): data is ApiErrorEnvelope {
  return (
    typeof data === "object" &&
    data !== null &&
    "success" in data &&
    (data as { success: unknown }).success === false &&
    "error" in data &&
    typeof (data as { error: unknown }).error === "object" &&
    (data as { error: unknown }).error !== null
  );
}

/** Convert any thrown value from an API call into a safe, typed ApiError. */
export function normalizeApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? null;
    const data = error.response?.data;

    if (isErrorEnvelope(data)) {
      return new ApiError({
        code: data.error.code,
        message: data.error.message,
        status,
        details: data.error.details ?? null,
      });
    }

    if (error.code === "ECONNABORTED") {
      return new ApiError({
        code: "REQUEST_TIMEOUT",
        message: "The request took too long to respond. Please try again.",
        status,
      });
    }

    if (!error.response) {
      return new ApiError({
        code: "NETWORK_ERROR",
        message:
          "Unable to reach the AVAP backend. Check your connection and try again.",
        status: null,
      });
    }

    return new ApiError({
      code: "UNEXPECTED_RESPONSE",
      message: "The server returned an unexpected response.",
      status,
    });
  }

  return new ApiError({
    code: "UNKNOWN_ERROR",
    message: "An unexpected error occurred. Please try again.",
    status: null,
  });
}
