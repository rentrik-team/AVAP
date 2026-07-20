"use client";

import { Crosshair, FileText, Network, Radar, Server, ShieldAlert, Bug } from "lucide-react";

import { ErrorState } from "@/components/shared/error-state";
import { MetricCard } from "@/components/shared/metric-card";
import { MetricCardSkeleton } from "@/components/shared/skeletons";
import {
  useDashboardAssetStatistics,
  useDashboardSummary,
} from "@/features/dashboard/hooks/use-dashboard";
import { formatCount } from "@/utils/format";

const GRID_CLASS = "grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7";

export function CoreMetricCards() {
  const { data, isPending, isError, refetch } = useDashboardSummary();
  // Open network services (one row per open port) come from the asset
  // statistics endpoint — the executive summary doesn't carry this count.
  const { data: assetStats } = useDashboardAssetStatistics(1);

  if (isPending) {
    return (
      <div className={GRID_CLASS}>
        {Array.from({ length: 7 }).map((_, index) => (
          <MetricCardSkeleton key={index} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load platform metrics"
        description="Executive summary metrics could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  const metrics = [
    { label: "Targets", value: data.total_targets, icon: Crosshair },
    { label: "Scans", value: data.total_scans, icon: Radar },
    { label: "Assets", value: data.total_assets, icon: Server },
    {
      label: "Open services",
      value: assetStats?.total_network_services ?? 0,
      icon: Network,
    },
    {
      label: "Unique vulnerabilities",
      value: data.unique_vulnerability_count,
      icon: Bug,
    },
    {
      label: "Critical vulnerabilities",
      value: data.critical_vulnerability_count,
      icon: ShieldAlert,
    },
    { label: "Reports generated", value: data.total_reports_generated, icon: FileText },
  ];

  return (
    <div className={GRID_CLASS}>
      {metrics.map((metric) => (
        <MetricCard
          key={metric.label}
          label={metric.label}
          value={formatCount(metric.value)}
          icon={metric.icon}
        />
      ))}
    </div>
  );
}
