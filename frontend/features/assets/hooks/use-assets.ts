import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { assetsApi } from "@/features/assets/api/assets-api";
import { assetKeys } from "@/features/assets/hooks/query-keys";
import type { AssetListFilters } from "@/features/assets/types/asset";
import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import type { ApiError } from "@/lib/api/errors";

/**
 * Assets are a discovered inventory/catalog resource, not an actively
 * observed lifecycle (unlike Scans) — there is no operational justification
 * for periodic polling here (frontend.md/Backend_Walk.md only document
 * polling for Dashboard aggregates and active scan status). Standard
 * TanStack Query staleness/refetch-on-mount behavior is sufficient.
 */
export function useAssets(params: { skip?: number; limit?: number } & AssetListFilters = {}) {
  const query = {
    skip: params.skip ?? 0,
    limit: params.limit ?? 50,
    ip: params.ip,
    hostname: params.hostname,
    port: params.port,
    cve: params.cve,
    target_id: params.target_id,
  };
  return useQuery({
    queryKey: assetKeys.list(query),
    queryFn: () => assetsApi.getAssets(query),
  });
}

export function useAsset(assetId: string) {
  return useQuery({
    queryKey: assetKeys.detail(assetId),
    queryFn: () => assetsApi.getAsset(assetId),
    enabled: Boolean(assetId),
  });
}

/**
 * No `retry`: delete is not idempotent-safe to replay automatically.
 *
 * Cache invalidation is derived from the verified FK cascade chain
 * (backend/app/models/{service,scan_finding,risk_assessment,ai_recommendation}.py,
 * all `ondelete="CASCADE"` on asset_id or a chain rooted in it) cross-referenced
 * against Module 09's metric ownership (app/repositories/dashboard_repository.py):
 *
 * - assets.id deleted -> services (asset_id CASCADE), scan_findings (asset_id
 *   CASCADE), risk_assessments (asset_id CASCADE, both ASSET- and
 *   VULNERABILITY-scope rows for this asset) -> ai_recommendations
 *   (risk_assessment_id CASCADE).
 * - dashboard/summary.total_assets and .high_risk_asset_count: affected
 *   (count_assets() + risk distribution).
 * - dashboard/assets: affected (total_assets, recently_discovered_assets).
 * - dashboard/vulnerabilities: affected via finding_count
 *   (count_scan_findings()) — but NOT unique_vulnerability_count or
 *   severity_distribution, which query the untouched `vulnerabilities`
 *   catalog table directly.
 * - dashboard/risk: affected (risk_level_distribution, top_risk_assets
 *   read from the cascaded risk_assessments rows).
 * - dashboard/ai: affected (recommendation counts read from the cascaded
 *   ai_recommendations rows).
 * - dashboard/scans and dashboard/reports: NOT affected — scan_jobs and
 *   reports have no FK path from assets.
 * - vulnerabilityKeys (the Vulnerability catalog cache): NOT invalidated —
 *   the `vulnerabilities` table itself is never touched by asset deletion.
 */
export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: (assetId: string) => assetsApi.deleteAsset(assetId),
    onSuccess: (_data, assetId) => {
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
      queryClient.removeQueries({ queryKey: assetKeys.detail(assetId) });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "assets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "vulnerabilities"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "risk"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "ai"] });
    },
  });
}
