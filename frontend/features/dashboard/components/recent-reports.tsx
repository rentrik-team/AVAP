"use client";

import { FileText } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { useDashboardReportStatistics } from "@/features/dashboard/hooks/use-dashboard";
import { formatCount, formatRelativeTime } from "@/utils/format";

export function RecentReports() {
  const { data, isPending, isError, refetch } = useDashboardReportStatistics();

  if (isPending) return <ListRowsSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load report activity"
        description="Report generation statistics could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  if (data.recent_reports.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No reports generated yet"
        description="Generated reports will appear here once a scan's risk has been assessed and reported."
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted-foreground">
        {formatCount(data.total_reports_generated)} total
        {data.latest_report_generated_at &&
          ` · latest ${formatRelativeTime(data.latest_report_generated_at)}`}
      </p>
      <ul className="flex flex-col divide-y divide-border">
        {data.recent_reports.map((report) => (
          <li key={report.report_id} className="flex items-center justify-between gap-3 py-2.5">
            <div className="flex min-w-0 flex-col">
              <span className="text-sm uppercase text-foreground">{report.format}</span>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(report.generated_at)}
              </span>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <RiskScore score={report.overall_risk_score} />
              <RiskLevelBadge level={report.overall_risk_level} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
