"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, OctagonX, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CopyableValue } from "@/components/shared/copyable-value";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { ScanStatusBadge } from "@/components/shared/scan-status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AssetList } from "@/features/assets/components/asset-list";
import { assetKeys } from "@/features/assets/hooks/query-keys";
import { dashboardKeys } from "@/features/dashboard/hooks/query-keys";
import { ScanReportsSection } from "@/features/reports/components/scan-reports-section";
import { RiskList } from "@/features/risk/components/risk-list";
import { ScanRiskSection } from "@/features/risk/components/scan-risk-section";
import { DeleteScanDialog } from "@/features/scans/components/delete-scan-dialog";
import { scanKeys } from "@/features/scans/hooks/query-keys";
import {
  isTerminalScanStatus,
  useCancelScan,
  useScan,
  useScanStatus,
} from "@/features/scans/hooks/use-scans";
import type { ScanStatus } from "@/features/scans/types/scan";
import { useTarget } from "@/features/targets/hooks/use-targets";
import { VulnerabilityList } from "@/features/vulnerabilities/components/vulnerability-list";
import { vulnerabilityKeys } from "@/features/vulnerabilities/hooks/query-keys";
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
  const [rawOutputOpen, setRawOutputOpen] = useState(false);
  const { data: scan, isPending, isError, refetch } = useScan(scanId);
  const { data: statusData } = useScanStatus(scanId);
  const { data: target } = useTarget(scan?.target_id ?? "");
  const previousStatusRef = useRef<ScanStatus | undefined>(undefined);
  const { mutate: cancelScan, isPending: isCancelling } = useCancelScan();

  // Lifecycle observation: when the polled lightweight status transitions
  // into a terminal state, pull the final full record (completed_at,
  // execution_duration, failure_reason) and refresh the read models it
  // affects — including the asset inventory and vulnerability findings the
  // completed scan just populated (AI discovery runs server-side as part
  // of scan completion). This never triggers risk/AI/report orchestration
  // itself — it only re-reads what the backend has already persisted.
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
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: vulnerabilityKeys.lists() });
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

  function handleCancel() {
    if (isCancelling) return;
    cancelScan(scanId, {
      onSuccess: () => {
        toast.success("Cancellation requested — the scan will stop shortly");
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title={`${formatLabel(scan.scan_type)} Scan`}
        actions={
          <div className="flex items-center gap-2">
            {isRunning && (
              <Button variant="outline" onClick={handleCancel} disabled={isCancelling}>
                <OctagonX className="size-4" aria-hidden="true" />
                {isCancelling ? "Cancelling…" : "Stop Scan"}
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => setDeleteOpen(true)}
              disabled={isRunning}
              title={isRunning ? "Cannot delete a running scan" : undefined}
            >
              <Trash2 className="size-4" aria-hidden="true" />
              Delete
            </Button>
          </div>
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

      <Card>
        <CardHeader>
          <CardTitle>Discovered Hosts &amp; Services</CardTitle>
          <CardDescription>
            What the scanner found — hosts, operating systems, open ports,
            protocols, running services, and detected versions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AssetList scanId={scan.scan_id} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security Analysis</CardTitle>
          <CardDescription>
            Potential vulnerabilities for this scan&apos;s discovered services.
            Entries marked AI-assisted are inferences from service and version
            banners — not scanner-confirmed results.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <VulnerabilityList scanId={scan.scan_id} />
        </CardContent>
      </Card>

      <ScanRiskSection scanId={scan.scan_id} scanStatus={scan.status} />

      <Card>
        <CardHeader>
          <CardTitle>Findings &amp; Remediation</CardTitle>
          <CardDescription>
            Deterministic risk-scored findings from the Risk Engine. Open a
            vulnerability finding to generate advisory AI remediation guidance.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RiskList scanId={scan.scan_id} />
        </CardContent>
      </Card>

      <ScanReportsSection scanId={scan.scan_id} scanStatus={scan.status} />

      {(scan.stdout_log || scan.stderr_log) && (
        <Card>
          <CardHeader>
            <button
              type="button"
              className="flex w-full items-center gap-2 text-left"
              onClick={() => setRawOutputOpen((prev) => !prev)}
              aria-expanded={rawOutputOpen}
            >
              {rawOutputOpen ? (
                <ChevronDown className="size-4 shrink-0" aria-hidden="true" />
              ) : (
                <ChevronRight className="size-4 shrink-0" aria-hidden="true" />
              )}
              <CardTitle>Raw Scanner Output</CardTitle>
            </button>
            <CardDescription>
              Unprocessed scanner logs
              {scan.status === "CANCELLED" || scan.status === "RUNNING"
                ? " (partial — scan was stopped before finishing)"
                : ""}
              . Everything above is parsed and normalized from this output.
            </CardDescription>
          </CardHeader>
          {rawOutputOpen && (
            <CardContent className="flex flex-col gap-3">
              {scan.stdout_log && (
                <pre className="max-h-80 overflow-auto rounded-md border border-border bg-muted/50 px-3 py-2 font-mono text-xs text-foreground whitespace-pre-wrap">
                  {scan.stdout_log}
                </pre>
              )}
              {scan.stderr_log && (
                <pre className="max-h-80 overflow-auto rounded-md border border-destructive-border bg-destructive-bg px-3 py-2 font-mono text-xs text-destructive whitespace-pre-wrap">
                  {scan.stderr_log}
                </pre>
              )}
            </CardContent>
          )}
        </Card>
      )}

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
