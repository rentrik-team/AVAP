import { useQuery } from "@tanstack/react-query";

import { vulnerabilityKeys } from "@/features/vulnerabilities/hooks/query-keys";
import { vulnerabilitiesApi } from "@/features/vulnerabilities/api/vulnerabilities-api";
import type { VulnerabilityListFilters } from "@/features/vulnerabilities/types/vulnerability";

/**
 * The Vulnerability catalog is a read-only reference/inventory resource —
 * no mutation hooks exist here (no endpoint to call), and no polling is
 * applied for the same reason as Assets (catalog data, not an actively
 * observed lifecycle).
 */
export function useVulnerabilities(
  params: { skip?: number; limit?: number } & VulnerabilityListFilters = {}
) {
  const query = {
    skip: params.skip ?? 0,
    limit: params.limit ?? 50,
    severity_rating: params.severity_rating,
    cve: params.cve,
    target_id: params.target_id,
    scan_id: params.scan_id,
  };
  return useQuery({
    queryKey: vulnerabilityKeys.list(query),
    queryFn: () => vulnerabilitiesApi.getVulnerabilities(query),
  });
}

export function useVulnerability(vulnerabilityId: string) {
  return useQuery({
    queryKey: vulnerabilityKeys.detail(vulnerabilityId),
    queryFn: () => vulnerabilitiesApi.getVulnerability(vulnerabilityId),
    enabled: Boolean(vulnerabilityId),
  });
}
