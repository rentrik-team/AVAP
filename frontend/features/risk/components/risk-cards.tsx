"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RiskLevelBadge } from "@/components/shared/risk-level-badge";
import { RiskScore } from "@/components/shared/risk-score";
import { resolveRiskEntityLink } from "@/features/risk/lib/entity-link";
import { RiskScopeBadge } from "@/features/risk/components/risk-scope-badge";
import type { RiskAssessmentResponse } from "@/features/risk/types/risk";
import { formatRelativeTime } from "@/utils/format";

/** Mobile transformation of the risk table — design_system.md §41. Score
 * and level are never hidden on mobile. */
export function RiskCards({
  assessments,
  onOpenRemediation,
}: {
  assessments: RiskAssessmentResponse[];
  onOpenRemediation: (assessment: RiskAssessmentResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {assessments.map((assessment) => {
        const entityLink = resolveRiskEntityLink(assessment);
        return (
          <Card key={assessment.id}>
            <CardContent className="flex flex-col gap-3">
              <div className="flex items-center justify-between gap-3">
                <RiskScopeBadge scope={assessment.scope} />
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(assessment.calculated_at)}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <RiskScore score={assessment.risk_score} className="text-h3" />
                <RiskLevelBadge level={assessment.risk_level} />
              </div>
              <div className="flex items-center justify-between gap-3">
                {entityLink ? (
                  <Link
                    href={entityLink.href}
                    className="truncate font-mono text-xs text-foreground hover:text-primary hover:underline"
                  >
                    {entityLink.label}
                  </Link>
                ) : (
                  <span className="text-xs text-muted-foreground">Platform-wide</span>
                )}
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
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
