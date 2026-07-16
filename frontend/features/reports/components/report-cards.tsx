"use client";

import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { ReportRowActions } from "@/features/reports/components/report-row-actions";
import type { ReportResponse } from "@/features/reports/types/report";
import { formatCount, formatRelativeTime } from "@/utils/format";

/** Mobile transformation of the report table — design_system.md §41. */
export function ReportCards({
  reports,
  onDeleteRequest,
}: {
  reports: ReportResponse[];
  onDeleteRequest: (report: ReportResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {reports.map((report) => (
        <Card key={report.id}>
          <CardContent className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-3">
              <Link
                href={`/reports/${report.id}`}
                className="text-sm font-medium text-foreground hover:text-primary hover:underline"
              >
                {report.format} Report
              </Link>
              <ReportRowActions report={report} onDeleteRequest={onDeleteRequest} />
            </div>
            <div className="flex items-center gap-2">
              <RiskScore score={report.overall_risk_score} />
              <RiskLevelBadge level={report.overall_risk_level} />
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground">
                {formatCount(report.vulnerability_count)} findings
              </span>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(report.generated_at)}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
