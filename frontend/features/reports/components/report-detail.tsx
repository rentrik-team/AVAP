"use client";

import { Download, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { Skeleton } from "@/components/ui/skeleton";
import { DeleteReportDialog } from "@/features/reports/components/delete-report-dialog";
import { useDownloadReport, useReport } from "@/features/reports/hooks/use-reports";
import { triggerBrowserDownload } from "@/features/reports/lib/download";
import { formatCount, formatDateTime, formatFileSize } from "@/utils/format";

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  );
}

export function ReportDetail({ reportId }: { reportId: string }) {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { data: report, isPending, isError, refetch } = useReport(reportId);
  const { mutate: download, isPending: isDownloading } = useDownloadReport();

  function handleDownload() {
    if (isDownloading) return;
    download(reportId, {
      onSuccess: (blob) => triggerBrowserDownload(blob, `avap-report-${reportId}.pdf`),
      onError: (error) => toast.error(error.message),
    });
  }

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

  if (isError || !report) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col">
        <PageHeader title="Report" />
        <ErrorState
          title="Unable to load this report"
          description="The report metadata could not be retrieved."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
      <PageHeader
        title={`${report.format} Report`}
        actions={
          <div className="flex items-center gap-2">
            <Button onClick={handleDownload} disabled={isDownloading}>
              <Download className="size-4" aria-hidden="true" />
              {isDownloading ? "Downloading…" : "Download"}
            </Button>
            <Button variant="outline" onClick={() => setDeleteOpen(true)}>
              <Trash2 className="size-4" aria-hidden="true" />
              Delete
            </Button>
          </div>
        }
      />

      <Card>
        <CardContent className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <DetailField label="Scan">
            <Link
              href={`/scans/${report.scan_id}`}
              className="font-mono text-xs text-foreground hover:text-primary hover:underline"
            >
              {report.scan_id}
            </Link>
          </DetailField>
          <DetailField label="Overall risk">
            <div className="flex items-center gap-2">
              <RiskScore score={report.overall_risk_score} />
              <RiskLevelBadge level={report.overall_risk_level} />
            </div>
          </DetailField>
          <DetailField label="Vulnerability count">
            {formatCount(report.vulnerability_count)}
          </DetailField>
          <DetailField label="AI recommendations included">
            {formatCount(report.ai_recommendations_included)}
          </DetailField>
          <DetailField label="File size">{formatFileSize(report.file_size_bytes)}</DetailField>
          <DetailField label="Generated">{formatDateTime(report.generated_at)}</DetailField>
          <DetailField label="Report template version">
            {report.report_template_version}
          </DetailField>
          <DetailField label="Risk calculation version">
            {report.risk_calculation_version}
          </DetailField>
        </CardContent>
      </Card>

      <DeleteReportDialog
        report={report}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onDeleted={() => router.push("/reports")}
      />
    </div>
  );
}
