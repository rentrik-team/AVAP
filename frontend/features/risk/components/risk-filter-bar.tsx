"use client";

import { FilterMenu } from "@/components/shared/filter-menu";
import type { RiskLevel, RiskListFilters, RiskScope } from "@/features/risk/types/risk";

const SCOPE_OPTIONS: { label: string; value: RiskScope | "" }[] = [
  { label: "All scopes", value: "" },
  { label: "Vulnerability", value: "VULNERABILITY" },
  { label: "Asset", value: "ASSET" },
  { label: "Scan", value: "SCAN" },
  { label: "Assessment", value: "ASSESSMENT" },
];

const LEVEL_OPTIONS: { label: string; value: RiskLevel | "" }[] = [
  { label: "All levels", value: "" },
  { label: "Critical", value: "CRITICAL" },
  { label: "High", value: "HIGH" },
  { label: "Medium", value: "MEDIUM" },
  { label: "Low", value: "LOW" },
  { label: "Informational", value: "INFORMATIONAL" },
];

export function RiskFilterBar({
  scope,
  riskLevel,
  onFilterChange,
}: {
  scope: RiskScope | "";
  riskLevel: RiskLevel | "";
  onFilterChange: (filters: RiskListFilters) => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-foreground">Scope</span>
        <FilterMenu
          label="Filter by scope"
          options={SCOPE_OPTIONS}
          value={scope}
          onChange={(next) =>
            onFilterChange({
              scope: next || undefined,
              risk_level: riskLevel || undefined,
            })
          }
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-foreground">Risk level</span>
        <FilterMenu
          label="Filter by risk level"
          options={LEVEL_OPTIONS}
          value={riskLevel}
          onChange={(next) =>
            onFilterChange({
              scope: scope || undefined,
              risk_level: next || undefined,
            })
          }
        />
      </div>
    </div>
  );
}
