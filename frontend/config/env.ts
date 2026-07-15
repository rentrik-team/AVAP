import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z
    .string()
    .min(1, "NEXT_PUBLIC_API_BASE_URL is not set.")
    .url(
      "NEXT_PUBLIC_API_BASE_URL must be a valid absolute URL, e.g. https://api.example.com"
    ),
});

function loadEnv() {
  const parsed = envSchema.safeParse({
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
  });

  if (!parsed.success) {
    const issues = parsed.error.issues.map((issue) => issue.message).join(" ");
    throw new Error(
      `Invalid frontend environment configuration: ${issues} Copy ` +
        "frontend/.env.example to frontend/.env.local and set it before starting the app."
    );
  }

  return {
    apiBaseUrl: parsed.data.NEXT_PUBLIC_API_BASE_URL.replace(/\/+$/, ""),
    apiVersionPrefix: "/api/v1",
  } as const;
}

export const env = loadEnv();
