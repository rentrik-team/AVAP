/**
 * Mirrors the backend's standardized response envelope
 * (app.api.responses.api_response.SuccessResponse / ErrorResponse).
 * Every AVAP REST endpoint uses this shape.
 */

export interface ApiErrorDetails {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ApiSuccessEnvelope<T> {
  success: true;
  data: T;
  error: null;
}

export interface ApiErrorEnvelope {
  success: false;
  data: null;
  error: ApiErrorDetails;
}

export type ApiEnvelope<T> = ApiSuccessEnvelope<T> | ApiErrorEnvelope;
