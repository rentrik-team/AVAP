import axios from "axios";

import { env } from "@/config/env";

/**
 * Single centralized Axios instance. Owns transport concerns only (base
 * URL, timeout, default headers) — never business logic or response
 * unwrapping. Every feature service function calls this instance and
 * unwraps its own response via `requestData` (lib/api/request.ts).
 */
export const apiClient = axios.create({
  baseURL: `${env.apiBaseUrl}${env.apiVersionPrefix}`,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});
