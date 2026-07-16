"use client";

import { Radar } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { DeleteScanDialog } from "@/features/scans/components/delete-scan-dialog";
import { ScanCards } from "@/features/scans/components/scan-cards";
import { ScanTable } from "@/features/scans/components/scan-table";
import { useScans } from "@/features/scans/hooks/use-scans";
import type { ScanResponse } from "@/features/scans/types/scan";
// Resolving each scan's target identity is read-only composition against
// the Targets feature's own public hook — Scan API communication still
// only happens inside features/scans/api.
import { useTargets } from "@/features/targets/hooks/use-targets";
import type { TargetResponse } from "@/features/targets/types/target";
import { formatCount } from "@/utils/format";

const PAGE_SIZE = 50;
// The backend has no "get targets by ids" batch endpoint, so target
// identity for the scan list is resolved from one bounded lookup page
// (the maximum the API allows) rather than per-row requests. Beyond this
// many targets, unresolved rows fall back to the raw target_id rather than
// silently guessing — see ScanTable/ScanCards.
const TARGET_LOOKUP_LIMIT = 200;

export function ScanList() {
  const [skip, setSkip] = useState(0);
  const [scanPendingDelete, setScanPendingDelete] = useState<ScanResponse | null>(null);
  const { data, isPending, isError, refetch } = useScans({ skip, limit: PAGE_SIZE });
  const { data: targetsData } = useTargets({ limit: TARGET_LOOKUP_LIMIT });

  const targetsById = useMemo(() => {
    const map = new Map<string, TargetResponse>();
    for (const target of targetsData?.targets ?? []) {
      map.set(target.id, target);
    }
    return map;
  }, [targetsData]);

  if (isPending) {
    return <ListRowsSkeleton rows={6} />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load scans"
        description="Scan history could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  if (data.scans.length === 0) {
    return (
      <EmptyState
        icon={Radar}
        title="No scans yet"
        description="Start a scan from a target to begin assessing it."
      />
    );
  }

  const rangeStart = skip + 1;
  const rangeEnd = Math.min(skip + PAGE_SIZE, data.total);

  return (
    <div className="flex flex-col gap-4">
      <ScanTable
        scans={data.scans}
        targetsById={targetsById}
        onDeleteRequest={setScanPendingDelete}
      />
      <ScanCards
        scans={data.scans}
        targetsById={targetsById}
        onDeleteRequest={setScanPendingDelete}
      />

      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          Showing {formatCount(rangeStart)}–{formatCount(rangeEnd)} of{" "}
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

      {scanPendingDelete && (
        <DeleteScanDialog
          scan={scanPendingDelete}
          open
          onOpenChange={(next) => {
            if (!next) setScanPendingDelete(null);
          }}
        />
      )}
    </div>
  );
}
