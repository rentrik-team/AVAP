"use client";

import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { FilterMenu } from "@/components/shared/filter-menu";
import type {
  AuditActorType,
  AuditEventCategory,
  AuditEventListFilters,
  AuditEventType,
  AuditOutcome,
  AuditResourceType,
} from "@/features/audit/types/audit";
import { formatEnumLabel } from "@/utils/format";

const EVENT_TYPE_VALUES: AuditEventType[] = [
  "TARGET_CREATED",
  "TARGET_UPDATED",
  "TARGET_DELETED",
  "SCAN_CREATED",
  "SCAN_DELETED",
  "INVENTORY_PROCESSED",
  "INVENTORY_PROCESSING_FAILED",
  "RISK_CALCULATION_COMPLETED",
  "RISK_CALCULATION_FAILED",
  "AI_RECOMMENDATION_GENERATED",
  "AI_RECOMMENDATION_FAILED",
  "REPORT_GENERATED",
  "REPORT_GENERATION_FAILED",
  "REPORT_DOWNLOADED",
  "REPORT_DELETED",
];

const CATEGORY_VALUES: AuditEventCategory[] = [
  "TARGET",
  "SCAN",
  "INVENTORY",
  "RISK",
  "AI",
  "REPORT",
  "SYSTEM",
];

const OUTCOME_VALUES: AuditOutcome[] = ["SUCCESS", "FAILURE"];

const RESOURCE_TYPE_VALUES: AuditResourceType[] = [
  "TARGET",
  "SCAN",
  "RISK_ASSESSMENT",
  "AI_RECOMMENDATION",
  "REPORT",
];

const ACTOR_TYPE_VALUES: AuditActorType[] = ["SYSTEM", "ANONYMOUS"];

function toOptions<T extends string>(values: T[], allLabel: string) {
  return [
    { label: allLabel, value: "" as const },
    ...values.map((value) => ({ label: formatEnumLabel(value), value })),
  ];
}

const EVENT_TYPE_OPTIONS = toOptions(EVENT_TYPE_VALUES, "All event types");
const CATEGORY_OPTIONS = toOptions(CATEGORY_VALUES, "All categories");
const OUTCOME_OPTIONS = toOptions(OUTCOME_VALUES, "All outcomes");
const RESOURCE_TYPE_OPTIONS = toOptions(RESOURCE_TYPE_VALUES, "All resource types");
const ACTOR_TYPE_OPTIONS = toOptions(ACTOR_TYPE_VALUES, "All actors");

export function AuditFilterBar({
  filters,
  scanIdChip,
  onFilterChange,
  onClearScanId,
}: {
  filters: AuditEventListFilters;
  /** Set only when scan_id was seeded from a "?scan_id=" deep link
   * (e.g. Scan Detail's "View audit history" link) — shown as a removable
   * chip rather than a manual UUID-entry field. */
  scanIdChip: string | null;
  onFilterChange: (filters: AuditEventListFilters) => void;
  onClearScanId: () => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Event type</span>
          <FilterMenu
            label="Filter by event type"
            options={EVENT_TYPE_OPTIONS}
            value={filters.event_type ?? ""}
            onChange={(value) =>
              onFilterChange({ ...filters, event_type: value || undefined })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Category</span>
          <FilterMenu
            label="Filter by category"
            options={CATEGORY_OPTIONS}
            value={filters.category ?? ""}
            onChange={(value) =>
              onFilterChange({ ...filters, category: value || undefined })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Outcome</span>
          <FilterMenu
            label="Filter by outcome"
            options={OUTCOME_OPTIONS}
            value={filters.outcome ?? ""}
            onChange={(value) =>
              onFilterChange({ ...filters, outcome: value || undefined })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Resource type</span>
          <FilterMenu
            label="Filter by resource type"
            options={RESOURCE_TYPE_OPTIONS}
            value={filters.resource_type ?? ""}
            onChange={(value) =>
              onFilterChange({ ...filters, resource_type: value || undefined })
            }
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-foreground">Actor</span>
          <FilterMenu
            label="Filter by actor type"
            options={ACTOR_TYPE_OPTIONS}
            value={filters.actor_type ?? ""}
            onChange={(value) =>
              onFilterChange({ ...filters, actor_type: value || undefined })
            }
          />
        </div>
      </div>

      {scanIdChip && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Active filter:</span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-2.5 py-1 text-xs text-foreground">
            Scan: <span className="font-mono">{scanIdChip.slice(0, 8)}</span>
            <Button
              variant="ghost"
              size="icon-xs"
              aria-label="Clear scan filter"
              onClick={onClearScanId}
              className="ml-0.5 size-4"
            >
              <X className="size-3" aria-hidden="true" />
            </Button>
          </span>
        </div>
      )}
    </div>
  );
}
