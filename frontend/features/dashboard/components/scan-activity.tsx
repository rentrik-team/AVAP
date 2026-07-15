"use client";

import { Radar } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ScanStatusBadge } from "@/components/shared/scan-status-badge";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { useDashboardScanStatistics } from "@/features/dashboard/hooks/use-dashboard";
import { formatDuration, formatPercent, formatRelativeTime } from "@/utils/format";

export function ScanActivity() {
  const { data, isPending, isError, refetch } = useDashboardScanStatistics();

  if (isPending) return <ListRowsSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load scan activity"
        description="Scan execution statistics could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg bg-muted/50 px-3 py-2.5 text-sm">
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Success rate</span>
          <span className="font-mono font-semibold tabular-nums">
            {formatPercent(data.scan_success_rate_percent)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Avg. duration</span>
          <span className="font-mono font-semibold tabular-nums">
            {formatDuration(data.average_scan_duration_seconds)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground">Running now</span>
          <span className="font-mono font-semibold tabular-nums">
            {data.scans_by_status.running}
          </span>
        </div>
      </div>

      {data.recent_scans.length === 0 ? (
        <EmptyState
          icon={Radar}
          title="No scans yet"
          description="Recent scan activity will appear here once a scan runs."
        />
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {data.recent_scans.map((scan) => (
            <li key={scan.scan_id} className="flex items-center justify-between gap-3 py-2.5">
              <div className="flex min-w-0 flex-col">
                <span className="truncate font-mono text-sm text-foreground">
                  {scan.target}
                </span>
                <span className="text-xs text-muted-foreground">
                  {scan.started_at
                    ? formatRelativeTime(scan.started_at)
                    : "Not started yet"}
                  {scan.execution_duration_seconds !== null &&
                    ` · ${formatDuration(scan.execution_duration_seconds)}`}
                </span>
              </div>
              <ScanStatusBadge status={scan.status} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
