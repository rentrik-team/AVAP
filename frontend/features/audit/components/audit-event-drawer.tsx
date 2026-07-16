"use client";

import Link from "next/link";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { CopyableValue } from "@/components/shared/copyable-value";
import { AuditOutcomeBadge } from "@/features/audit/components/audit-outcome-badge";
import { EventMetadata } from "@/features/audit/components/event-metadata";
import { resolveAuditResourceLink } from "@/features/audit/lib/resource-link";
import type { AuditEventResponse } from "@/features/audit/types/audit";
import { formatDateTime, formatEnumLabel } from "@/utils/format";

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  );
}

export function AuditEventDrawer({
  event,
  open,
  onOpenChange,
}: {
  event: AuditEventResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const resourceLink = event ? resolveAuditResourceLink(event) : null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="data-[side=right]:sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Audit Event</SheetTitle>
          <SheetDescription>
            Immutable, read-only record. Audit events are never edited or deleted.
          </SheetDescription>
        </SheetHeader>

        {event && (
          <div className="flex flex-col gap-6 px-4 pb-6">
            <div className="flex items-center gap-3">
              <AuditOutcomeBadge outcome={event.outcome} />
              <span className="text-sm font-medium text-foreground">
                {formatEnumLabel(event.event_type)}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <DetailField label="Category">{formatEnumLabel(event.category)}</DetailField>
              <DetailField label="Occurred at">{formatDateTime(event.occurred_at)}</DetailField>
              <DetailField label="Actor type">{formatEnumLabel(event.actor_type)}</DetailField>
              <DetailField label="Actor ID">{event.actor_id ?? "—"}</DetailField>
              <DetailField label="Resource type">
                {event.resource_type ? formatEnumLabel(event.resource_type) : "—"}
              </DetailField>
              <DetailField label="Resource">
                {resourceLink ? (
                  <Link
                    href={resourceLink.href}
                    className="font-mono text-xs text-primary hover:underline"
                  >
                    {resourceLink.label}
                  </Link>
                ) : event.resource_id ? (
                  <CopyableValue value={event.resource_id} className="text-xs" />
                ) : (
                  "—"
                )}
              </DetailField>
              {event.scan_id && (
                <DetailField label="Scan">
                  <Link
                    href={`/scans/${event.scan_id}`}
                    className="font-mono text-xs text-primary hover:underline"
                  >
                    {event.scan_id}
                  </Link>
                </DetailField>
              )}
              <DetailField label="Request ID">
                {event.request_id ? (
                  <CopyableValue value={event.request_id} className="text-xs" />
                ) : (
                  "—"
                )}
              </DetailField>
              <DetailField label="Source IP">{event.source_ip ?? "—"}</DetailField>
            </div>

            <Separator />

            <div>
              <h3 className="text-title mb-3 text-foreground">Metadata</h3>
              <EventMetadata metadata={event.event_metadata} />
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
