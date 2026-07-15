"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "@/lib/api/errors";

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          // Client/business errors (4xx) are not transient — retrying
          // won't change the outcome. Only retry likely-transient
          // failures (network errors, 5xx), and only a couple of times.
          if (error instanceof ApiError && error.status !== null && error.status < 500) {
            return false;
          }
          return failureCount < 2;
        },
      },
    },
  });
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  // Created once per browser session (or once per request on the server),
  // never module-scoped — sharing a QueryClient across requests would leak
  // cached data between unrelated users on the server.
  const [queryClient] = useState(createQueryClient);

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
