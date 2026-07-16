"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CopyableValue } from "@/components/shared/copyable-value";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { ScanStatusBadge } from "@/components/shared/scan-status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import { ScanReportsSection } from "@/features/reports/components/scan-reports-section";
import { ScanRiskSection } from "@/features/risk/components/scan-risk-section";
import { DeleteScanDialog } from "@/features/scans/components/delete-scan-dialog";
import { scanKeys } from "@/features/scans/hooks/query-keys";
import {
  isTerminalScanStatus,
  useScan,
  useScanStatus,
} from "@/features/scans/hooks/use-scans";
import type { ScanStatus } from "@/features/scans/types/scan";
import { useTarget } from "@/features/targets/hooks/use-targets";
import { formatDateTime, formatDuration, formatLabel } from "@/utils/format";

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  );
}

export function ScanDetail({ scanId }: { scanId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { data: scan, isPending, isError, refetch } = useScan(scanId);
  const { data: statusData } = useScanStatus(scanId);
  const { data: target } = useTarget(scan?.target_id ?? "");
  const previousStatusRef = useRef<ScanStatus | undefined>(undefined);

  // Lifecycle observation: when the polled lightweight status transitions
  // into a terminal state, pull the final full record (completed_at,
  // execution_duration, failure_reason) and refresh the read models it
  // affects. This never triggers risk/AI/report orchestration itself —
  // it only re-reads what the backend has already persisted.
  useEffect(() => {
    const currentStatus = statusData?.status;
    if (!currentStatus) return;
    const previousStatus = previousStatusRef.current;
    if (
      previousStatus &&
      previousStatus !== currentStatus &&
      isTerminalScanStatus(currentStatus)
    ) {
      queryClient.invalidateQueries({ queryKey: scanKeys.detail(scanId) });
      queryClient.invalidateQueries({ queryKey: scanKeys.lists() });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.summary() });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "scans"] });
    }
    previousStatusRef.current = currentStatus;
  }, [statusData?.status, queryClient, scanId]);

  if (isPending) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Card>
          <CardContent className="flex flex-col gap-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError || !scan) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col">
        <PageHeader title="Scan" />
        <ErrorState
          title="Unable to load this scan"
          description="The scan record could not be retrieved."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const isRunning = scan.status === "RUNNING";

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title={`${formatLabel(scan.scan_type)} Scan`}
        actions={
          <Button
            variant="outline"
            onClick={() => setDeleteOpen(true)}
            disabled={isRunning}
            title={isRunning ? "Cannot delete a running scan" : undefined}
          >
            <Trash2 className="size-4" aria-hidden="true" />
            Delete
          </Button>
        }
      />

      <Card>
        <CardContent className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <DetailField label="Target">
            {target ? (
              <CopyableValue value={target.target} />
            ) : (
              <span className="font-mono text-xs text-muted-foreground">
                {scan.target_id}
              </span>
            )}
          </DetailField>

          <DetailField label="Status">
            <ScanStatusBadge status={scan.status} />
          </DetailField>

          <DetailField label="Started">
            {scan.started_at ? formatDateTime(scan.started_at) : "Not started yet"}
          </DetailField>

          <DetailField label="Completed">
            {scan.completed_at ? formatDateTime(scan.completed_at) : "—"}
          </DetailField>

          <DetailField label="Duration">
            {formatDuration(scan.execution_duration)}
          </DetailField>

          <DetailField label="Requested">{formatDateTime(scan.created_at)}</DetailField>

          {scan.failure_reason && (
            <div className="col-span-full flex flex-col gap-1">
              <span className="text-xs text-muted-foreground">Failure reason</span>
              <p className="rounded-md border border-destructive-border bg-destructive-bg px-3 py-2 text-sm text-destructive">
                {scan.failure_reason}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <ScanRiskSection scanId={scan.scan_id} scanStatus={scan.status} />

      <ScanReportsSection scanId={scan.scan_id} scanStatus={scan.status} />

      <Link
        href={`/audit?scan_id=${scan.scan_id}`}
        className="w-fit text-sm text-primary hover:underline"
      >
        View audit history for this scan →
      </Link>

      <DeleteScanDialog
        scan={scan}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onDeleted={() => router.push("/scans")}
      />
    </div>
  );
}
