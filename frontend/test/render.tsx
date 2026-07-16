import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";

import { TooltipProvider } from "@/components/ui/tooltip";

/** Fresh, retry-disabled QueryClient per test — no cross-test cache bleed. */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, refetchInterval: false },
    },
  });
}

/** Mirrors AppProviders' TooltipProvider ancestor — any shared component
 * that renders a Tooltip (e.g. table date columns) needs this context. */
export function renderWithQueryClient(ui: ReactElement) {
  const queryClient = createTestQueryClient();
  return {
    queryClient,
    ...render(
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>{ui}</TooltipProvider>
      </QueryClientProvider>
    ),
  };
}
