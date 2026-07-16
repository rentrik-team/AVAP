"use client";

import Link from "next/link";

import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ReportRowActions } from "@/features/reports/components/report-row-actions";
import type { ReportResponse } from "@/features/reports/types/report";
import { formatCount, formatDateTime, formatRelativeTime } from "@/utils/format";

export function ReportTable({
  reports,
  onDeleteRequest,
}: {
  reports: ReportResponse[];
  onDeleteRequest: (report: ReportResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Report</TableHead>
            <TableHead>Scan</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead>Findings</TableHead>
            <TableHead>Generated</TableHead>
            <TableHead className="w-12 text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {reports.map((report) => (
            <TableRow key={report.id} className="h-13">
              <TableCell>
                <Link
                  href={`/reports/${report.id}`}
                  className="text-sm font-medium text-foreground hover:text-primary hover:underline"
                >
                  {report.format} Report
                </Link>
              </TableCell>
              <TableCell>
                <Link
                  href={`/scans/${report.scan_id}`}
                  className="block truncate font-mono text-xs text-foreground hover:text-primary hover:underline"
                >
                  {report.scan_id}
                </Link>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <RiskScore score={report.overall_risk_score} />
                  <RiskLevelBadge level={report.overall_risk_level} />
                </div>
              </TableCell>
              <TableCell>
                <span className="text-sm text-muted-foreground">
                  {formatCount(report.vulnerability_count)} findings ·{" "}
                  {formatCount(report.ai_recommendations_included)} with guidance
                </span>
              </TableCell>
              <TableCell>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="text-sm text-muted-foreground">
                      {formatRelativeTime(report.generated_at)}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>{formatDateTime(report.generated_at)}</TooltipContent>
                </Tooltip>
              </TableCell>
              <TableCell className="text-right">
                <ReportRowActions report={report} onDeleteRequest={onDeleteRequest} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
