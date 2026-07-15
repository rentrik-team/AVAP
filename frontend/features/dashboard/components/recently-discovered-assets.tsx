"use client";

import { Server } from "lucide-react";

import { CopyableValue } from "@/components/shared/copyable-value";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { useDashboardAssetStatistics } from "@/features/dashboard/hooks/use-dashboard";
import { formatCount, formatRelativeTime } from "@/utils/format";

export function RecentlyDiscoveredAssets() {
  const { data, isPending, isError, refetch } = useDashboardAssetStatistics();

  if (isPending) return <ListRowsSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load asset inventory"
        description="Asset inventory statistics could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  if (data.recently_discovered_assets.length === 0) {
    return (
      <EmptyState
        icon={Server}
        title="No assets discovered yet"
        description="Discovered assets will appear here once a scan completes."
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground">
        {formatCount(data.total_network_services)} network services across{" "}
        {formatCount(data.total_assets)} assets
      </p>
      <ul className="flex flex-col divide-y divide-border">
        {data.recently_discovered_assets.map((asset) => (
          <li key={asset.asset_id} className="flex items-center justify-between gap-3 py-2.5">
            <div className="flex min-w-0 flex-col">
              <CopyableValue value={asset.ipv4} className="text-sm" />
              {asset.hostname && (
                <span className="truncate text-xs text-muted-foreground">
                  {asset.hostname}
                </span>
              )}
            </div>
            <span className="shrink-0 text-xs text-muted-foreground">
              {formatRelativeTime(asset.discovered_at)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
