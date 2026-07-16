"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AuditOutcomeBadge } from "@/features/audit/components/audit-outcome-badge";
import type { AuditEventResponse } from "@/features/audit/types/audit";
import { formatEnumLabel, formatRelativeTime } from "@/utils/format";

/** Mobile transformation of the audit table — design_system.md §41.
 * Outcome is never hidden on mobile. */
export function AuditCards({
  events,
  onViewDetail,
}: {
  events: AuditEventResponse[];
  onViewDetail: (event: AuditEventResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {events.map((event) => (
        <Card key={event.id}>
          <CardContent className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-3">
              <span className="text-sm font-medium text-foreground">
                {formatEnumLabel(event.event_type)}
              </span>
              <AuditOutcomeBadge outcome={event.outcome} />
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground">
                {formatEnumLabel(event.category)} · {formatEnumLabel(event.actor_type)}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(event.occurred_at)}
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="w-fit"
              onClick={() => onViewDetail(event)}
            >
              View details
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
