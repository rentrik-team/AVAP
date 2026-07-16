"use client";

import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { ScanStatusBadge } from "@/components/shared/scan-status-badge";
import { CopyableValue } from "@/components/shared/copyable-value";
import { ScanRowActions } from "@/features/scans/components/scan-row-actions";
import type { ScanResponse } from "@/features/scans/types/scan";
import type { TargetResponse } from "@/features/targets/types/target";
import { formatDuration, formatLabel, formatRelativeTime } from "@/utils/format";

/** Mobile transformation of the scan table — design_system.md §41. */
export function ScanCards({
  scans,
  targetsById,
  onDeleteRequest,
}: {
  scans: ScanResponse[];
  targetsById: Map<string, TargetResponse>;
  onDeleteRequest: (scan: ScanResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {scans.map((scan) => {
        const target = targetsById.get(scan.target_id);
        return (
          <Card key={scan.scan_id}>
            <CardContent className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 flex-col gap-1.5">
                <Link
                  href={`/scans/${scan.scan_id}`}
                  className="text-sm font-medium text-foreground hover:text-primary hover:underline"
                >
                  {formatLabel(scan.scan_type)} Scan
                </Link>
                {target ? (
                  <CopyableValue value={target.target} className="text-sm" />
                ) : (
                  <span className="font-mono text-xs text-muted-foreground">
                    {scan.target_id}
                  </span>
                )}
                <div className="flex items-center gap-2">
                  <ScanStatusBadge status={scan.status} />
                  <span className="text-xs text-muted-foreground">
                    {scan.started_at
                      ? formatRelativeTime(scan.started_at)
                      : "Not started"}
                    {scan.execution_duration !== null &&
                      ` · ${formatDuration(scan.execution_duration)}`}
                  </span>
                </div>
              </div>
              <ScanRowActions scan={scan} onDeleteRequest={onDeleteRequest} />
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
