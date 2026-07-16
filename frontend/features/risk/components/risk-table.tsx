"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
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
import { resolveRiskEntityLink } from "@/features/risk/lib/entity-link";
import { RiskScopeBadge } from "@/features/risk/components/risk-scope-badge";
import type { RiskAssessmentResponse } from "@/features/risk/types/risk";
import { formatDateTime, formatRelativeTime } from "@/utils/format";

export function RiskTable({
  assessments,
  onOpenRemediation,
}: {
  assessments: RiskAssessmentResponse[];
  onOpenRemediation: (assessment: RiskAssessmentResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Scope</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Level</TableHead>
            <TableHead>Identity</TableHead>
            <TableHead>Calculated</TableHead>
            <TableHead className="w-32 text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {assessments.map((assessment) => {
            const entityLink = resolveRiskEntityLink(assessment);
            return (
              <TableRow key={assessment.id} className="h-13">
                <TableCell>
                  <RiskScopeBadge scope={assessment.scope} />
                </TableCell>
                <TableCell>
                  <RiskScore score={assessment.risk_score} />
                </TableCell>
                <TableCell>
                  <RiskLevelBadge level={assessment.risk_level} />
                </TableCell>
                <TableCell className="max-w-56">
                  {entityLink ? (
                    <Link
                      href={entityLink.href}
                      className="block truncate font-mono text-xs text-foreground hover:text-primary hover:underline"
                    >
                      {entityLink.label}
                    </Link>
                  ) : (
                    <span className="text-xs text-muted-foreground">Platform-wide</span>
                  )}
                </TableCell>
                <TableCell>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-sm text-muted-foreground">
                        {formatRelativeTime(assessment.calculated_at)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>{formatDateTime(assessment.calculated_at)}</TooltipContent>
                  </Tooltip>
                </TableCell>
                <TableCell className="text-right">
                  {assessment.scope === "VULNERABILITY" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onOpenRemediation(assessment)}
                    >
                      <Sparkles className="size-4" aria-hidden="true" />
                      Remediation
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
