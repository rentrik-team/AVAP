"use client";

import { ScrollText, ShieldOff } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { AuditCards } from "@/features/audit/components/audit-cards";
import { AuditEventDrawer } from "@/features/audit/components/audit-event-drawer";
import { AuditFilterBar } from "@/features/audit/components/audit-filter-bar";
import { AuditTable } from "@/features/audit/components/audit-table";
import { useAuditEvents } from "@/features/audit/hooks/use-audit";
import type { AuditEventListFilters, AuditEventResponse } from "@/features/audit/types/audit";
import { formatCount } from "@/utils/format";

const PAGE_SIZE = 50;

/**
 * `initialScanId` seeds the scan filter from a one-time "?scan_id=" deep
 * link (e.g. Scan Detail's "View audit history for this scan" link) — read
 * once by the server component page and passed down as a prop, not a
 * two-way URL-sync architecture.
 */
export function AuditList({ initialScanId }: { initialScanId?: string }) {
  const [skip, setSkip] = useState(0);
  const [filters, setFilters] = useState<AuditEventListFilters>({});
  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [scanId, setScanId] = useState(initialScanId);
  const [selectedEvent, setSelectedEvent] = useState<AuditEventResponse | null>(null);

  const hasActiveFilters = Boolean(
    filters.event_type ||
      filters.category ||
      filters.outcome ||
      filters.resource_type ||
      filters.actor_type ||
      scanId
  );

  // Adjusted during render, not in an effect — see AssetList precedent.
  if (filters !== appliedFilters) {
    setAppliedFilters(filters);
    setSkip(0);
  }

  const { data, isPending, isError, refetch } = useAuditEvents({
    skip,
    limit: PAGE_SIZE,
    ...filters,
    scan_id: scanId,
  });

  function handleFilterChange(next: AuditEventListFilters) {
    setFilters(next);
  }

  return (
    <div className="flex flex-col gap-4">
      <AuditFilterBar
        filters={filters}
        scanIdChip={scanId ?? null}
        onFilterChange={handleFilterChange}
        onClearScanId={() => setScanId(undefined)}
      />

      {isPending ? (
        <ListRowsSkeleton rows={6} />
      ) : isError ? (
        <ErrorState
          title="Unable to load audit events"
          description="The audit trail could not be retrieved."
          onRetry={() => refetch()}
        />
      ) : data.events.length === 0 ? (
        hasActiveFilters ? (
          <EmptyState
            icon={ShieldOff}
            title="No audit events match these filters"
            description="Clear or adjust the active filters to see more results."
          />
        ) : (
          <EmptyState
            icon={ScrollText}
            title="No audit events recorded yet"
            description="Audit events are recorded automatically as platform actions occur."
          />
        )
      ) : (
        <>
          <AuditTable events={data.events} onViewDetail={setSelectedEvent} />
          <AuditCards events={data.events} onViewDetail={setSelectedEvent} />

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

      <AuditEventDrawer
        event={selectedEvent}
        open={Boolean(selectedEvent)}
        onOpenChange={(next) => {
          if (!next) setSelectedEvent(null);
        }}
      />
    </div>
  );
}
