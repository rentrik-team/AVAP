"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { AuditOutcomeBadge } from "@/features/audit/components/audit-outcome-badge";
import { resolveAuditResourceLink } from "@/features/audit/lib/resource-link";
import type { AuditEventResponse } from "@/features/audit/types/audit";
import { formatDateTime, formatEnumLabel, formatRelativeTime } from "@/utils/format";

export function AuditTable({
  events,
  onViewDetail,
}: {
  events: AuditEventResponse[];
  onViewDetail: (event: AuditEventResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Occurred</TableHead>
            <TableHead>Event</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Outcome</TableHead>
            <TableHead>Actor</TableHead>
            <TableHead>Resource</TableHead>
            <TableHead className="w-24 text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => {
            const resourceLink = resolveAuditResourceLink(event);
            return (
              <TableRow key={event.id} className="h-13">
                <TableCell>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-sm text-muted-foreground">
                        {formatRelativeTime(event.occurred_at)}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>{formatDateTime(event.occurred_at)}</TooltipContent>
                  </Tooltip>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-foreground">
                    {formatEnumLabel(event.event_type)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {formatEnumLabel(event.category)}
                  </span>
                </TableCell>
                <TableCell>
                  <AuditOutcomeBadge outcome={event.outcome} />
                </TableCell>
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {formatEnumLabel(event.actor_type)}
                  </span>
                </TableCell>
                <TableCell className="max-w-48">
                  {resourceLink ? (
                    <Link
                      href={resourceLink.href}
                      className="block truncate font-mono text-xs text-foreground hover:text-primary hover:underline"
                    >
                      {resourceLink.label}
                    </Link>
                  ) : event.resource_type ? (
                    <span className="text-xs text-muted-foreground">
                      {formatEnumLabel(event.resource_type)}
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" onClick={() => onViewDetail(event)}>
                    View
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
