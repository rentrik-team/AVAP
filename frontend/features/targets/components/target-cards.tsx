"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { TargetRowActions } from "@/features/targets/components/target-row-actions";
import { TARGET_TYPE_LABELS, type TargetResponse } from "@/features/targets/types/target";
import { formatRelativeTime } from "@/utils/format";

/** Mobile transformation of the target table — design_system.md §41: do not
 * squeeze a desktop table into a narrow viewport, use stacked cards instead. */
export function TargetCards({
  targets,
  onDeleteRequest,
}: {
  targets: TargetResponse[];
  onDeleteRequest: (target: TargetResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {targets.map((target) => (
        <Card key={target.id}>
          <CardContent className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 flex-col gap-1.5">
              <Link
                href={`/targets/${target.id}`}
                className="truncate font-mono text-sm font-medium text-foreground hover:text-primary hover:underline"
              >
                {target.target}
              </Link>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{TARGET_TYPE_LABELS[target.target_type]}</Badge>
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(target.created_at)}
                </span>
              </div>
            </div>
            <TargetRowActions target={target} onDeleteRequest={onDeleteRequest} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
