import { z } from "zod";

/**
 * UX-assist validation only — mirrors just the stable, documented backend
 * constraint (CreateTargetRequest.target: 1-253 chars,
 * backend/app/schemas/target.py). Format (IPv4/CIDR/hostname) is
 * deliberately NOT re-validated here: that is the backend's SSRF-aware
 * target-validation engine (app/core/security.py), and reimplementing it in
 * the browser would be a second, divergent security engine. The backend
 * remains the sole authority on whether a target value is acceptable.
 */
export const createTargetSchema = z.object({
  target: z
    .string()
    .min(1, "Enter a target to scan.")
    .max(253, "Target must be 253 characters or fewer."),
});

export type CreateTargetFormValues = z.infer<typeof createTargetSchema>;
