"use client";

import { Server, ShieldOff } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { AssetCards } from "@/features/assets/components/asset-cards";
import { AssetFilterBar } from "@/features/assets/components/asset-filter-bar";
import { AssetTable } from "@/features/assets/components/asset-table";
import { DeleteAssetDialog } from "@/features/assets/components/delete-asset-dialog";
import { useAssets } from "@/features/assets/hooks/use-assets";
import type { AssetListFilters, AssetResponse } from "@/features/assets/types/asset";
import { formatCount } from "@/utils/format";

const PAGE_SIZE = 50;

/** `targetId`, when given, scopes the list to assets discovered via scans
 * of that target (used by the Target detail page) instead of the global
 * inventory. Not user-editable via the filter bar — it's a fixed scope. */
export function AssetList({ targetId }: { targetId?: string } = {}) {
  const [skip, setSkip] = useState(0);
  const [filters, setFilters] = useState<AssetListFilters>({});
  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [assetPendingDelete, setAssetPendingDelete] = useState<AssetResponse | null>(
    null
  );

  const hasActiveFilters = Boolean(
    filters.ip || filters.hostname || filters.port || filters.cve
  );

  // Reset to the first page whenever the active filter set changes, so the
  // user is never stranded on a page beyond the new, smaller result set.
  // Adjusted during render (React's recommended pattern for "derive state
  // from a changed prop/value") rather than in a useEffect + setState,
  // which would cause an extra, avoidable commit.
  if (filters !== appliedFilters) {
    setAppliedFilters(filters);
    setSkip(0);
  }

  // Filters are user-controlled input passed straight through as Axios
  // query params (see assets-api.ts) — never concatenated into the URL.
  const { data, isPending, isError, refetch } = useAssets({
    skip,
    limit: PAGE_SIZE,
    ...filters,
    target_id: targetId,
  });

  return (
    <div className="flex flex-col gap-4">
      <AssetFilterBar onFilterChange={setFilters} />

      {isPending ? (
        <ListRowsSkeleton rows={6} />
      ) : isError ? (
        <ErrorState
          title="Unable to load assets"
          description="Asset inventory could not be retrieved."
          onRetry={() => refetch()}
        />
      ) : data.assets.length === 0 ? (
        hasActiveFilters ? (
          // The FilterBar above already renders its own "Clear filters"
          // control whenever a filter is active — no duplicate action here
          // (design_system.md §24's own filtered-empty example is
          // description-only, no button).
          <EmptyState
            icon={ShieldOff}
            title="No assets match these filters"
            description="Clear or adjust the active filters to see more results."
          />
        ) : (
          <EmptyState
            icon={Server}
            title="No assets have been discovered yet"
            description={
              targetId
                ? "Assets are populated automatically when a scan completes against this target. Start a scan to begin building the inventory."
                : "Assets are populated automatically when a scan completes against a target. Start a scan to begin building the inventory."
            }
          />
        )
      ) : (
        <>
          <AssetTable assets={data.assets} onDeleteRequest={setAssetPendingDelete} />
          <AssetCards assets={data.assets} onDeleteRequest={setAssetPendingDelete} />

          <div className="flex items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Showing {formatCount(skip + 1)}–{formatCount(Math.min(skip + PAGE_SIZE, data.total))} of{" "}
              {formatCount(data.total)}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSkip((prev) => Math.max(prev - PAGE_SIZE, 0))}
                disabled={skip === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSkip((prev) => prev + PAGE_SIZE)}
                disabled={skip + PAGE_SIZE >= data.total}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      {assetPendingDelete && (
        <DeleteAssetDialog
          asset={assetPendingDelete}
          open
          onOpenChange={(next) => {
            if (!next) setAssetPendingDelete(null);
          }}
        />
      )}
    </div>
  );
}
