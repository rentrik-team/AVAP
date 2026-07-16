"use client";

import { FileText } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { DeleteReportDialog } from "@/features/reports/components/delete-report-dialog";
import { ReportCards } from "@/features/reports/components/report-cards";
import { ReportTable } from "@/features/reports/components/report-table";
import { useReports } from "@/features/reports/hooks/use-reports";
import type { ReportResponse } from "@/features/reports/types/report";
import { formatCount } from "@/utils/format";

const PAGE_SIZE = 50;

/**
 * No scan_id filter control here: it's a real, tested backend parameter,
 * but a raw-UUID text box is poor UX for manual entry. The same filtering
 * capability is instead exposed contextually via ScanReportsSection (Scan
 * Detail already has an unambiguous scan_id) using the identical hook.
 */
export function ReportList() {
  const [skip, setSkip] = useState(0);
  const [reportPendingDelete, setReportPendingDelete] = useState<ReportResponse | null>(
    null
  );

  const { data, isPending, isError, refetch } = useReports({ skip, limit: PAGE_SIZE });

  return (
    <div className="flex flex-col gap-4">
      {isPending ? (
        <ListRowsSkeleton rows={6} />
      ) : isError ? (
        <ErrorState
          title="Unable to load reports"
          description="Report history could not be retrieved."
          onRetry={() => refetch()}
        />
      ) : data.reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No reports have been generated yet"
          description="Generate a report from a scan's detail page once its risk assessment has been calculated."
        />
      ) : (
        <>
          <ReportTable reports={data.reports} onDeleteRequest={setReportPendingDelete} />
          <ReportCards reports={data.reports} onDeleteRequest={setReportPendingDelete} />

          <div className="flex items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Showing {formatCount(skip + 1)}–
              {formatCount(Math.min(skip + PAGE_SIZE, data.total))} of{" "}
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

      {reportPendingDelete && (
        <DeleteReportDialog
          report={reportPendingDelete}
          open
          onOpenChange={(next) => {
            if (!next) setReportPendingDelete(null);
          }}
        />
      )}
    </div>
  );
}
