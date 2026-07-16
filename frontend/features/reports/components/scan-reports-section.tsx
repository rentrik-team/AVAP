"use client";

import { Download, FileText } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import {
  useDownloadReport,
  useGenerateReport,
  useReports,
} from "@/features/reports/hooks/use-reports";
import { triggerBrowserDownload } from "@/features/reports/lib/download";
import type { ScanStatus } from "@/features/scans/types/scan";
import { formatDateTime } from "@/utils/format";

/**
 * The single, deliberate Reports touchpoint on the Scan Detail page (Phase
 * 05, otherwise unmodified) — mirrors ScanRiskSection's precedent. Reuses
 * the exact same `useReports({ scan_id })` hook the main Reports page
 * uses, just with a fixed filter, rather than a second query path.
 */
export function ScanReportsSection({
  scanId,
  scanStatus,
}: {
  scanId: string;
  scanStatus: ScanStatus;
}) {
  const { data, isPending, isError } = useReports({ scan_id: scanId, limit: 10 });
  const { mutate: generate, isPending: isGenerating } = useGenerateReport();
  const { mutate: download, isPending: isDownloading } = useDownloadReport();

  // Report generation requires an already-calculated risk assessment for
  // the scan (backend returns 422 otherwise); restrained here the same way
  // ScanRiskSection restrains "Calculate Risk" to completed scans, rather
  // than inventing a second cross-feature fetch just to pre-validate it.
  const canGenerate = scanStatus === "COMPLETED";

  function handleGenerate() {
    if (isGenerating) return;
    generate(scanId, {
      onSuccess: () => toast.success("Report generated"),
      onError: (error) => toast.error(error.message),
    });
  }

  function handleDownload(reportId: string) {
    if (isDownloading) return;
    download(reportId, {
      onSuccess: (blob) => triggerBrowserDownload(blob, `avap-report-${reportId}.pdf`),
      onError: (error) => toast.error(error.message),
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reports</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {isPending ? (
          <ListRowsSkeleton rows={2} />
        ) : isError ? (
          <p className="text-sm text-muted-foreground">
            Reports for this scan could not be retrieved.
          </p>
        ) : data.reports.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No reports generated yet"
            description={
              canGenerate
                ? "Generate a report to capture this scan's current risk and remediation state."
                : "Reports can be generated once this scan completes and its risk is calculated."
            }
          />
        ) : (
          <ul className="flex flex-col divide-y divide-border">
            {data.reports.map((report) => (
              <li
                key={report.id}
                className="flex items-center justify-between gap-3 py-2.5"
              >
                <div className="flex flex-col">
                  <span className="text-sm text-foreground">{report.format} Report</span>
                  <span className="text-xs text-muted-foreground">
                    {formatDateTime(report.generated_at)}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDownload(report.id)}
                  disabled={isDownloading}
                >
                  <Download className="size-4" aria-hidden="true" />
                  Download
                </Button>
              </li>
            ))}
          </ul>
        )}

        {canGenerate && (
          <Button
            variant="outline"
            size="sm"
            className="w-fit"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating…" : "Generate Report"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
