"use client";

import { ShieldQuestion } from "lucide-react";
import { useReducedMotion } from "motion/react";
import { Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { ChartSkeleton } from "@/components/shared/skeletons";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { SEVERITY_META, SEVERITY_ORDER } from "@/constants/severity";
import { useDashboardVulnerabilityStatistics } from "@/features/dashboard/hooks/use-dashboard";
import { formatCount } from "@/utils/format";

export function SeverityDistributionChart() {
  const { data, isPending, isError, refetch } = useDashboardVulnerabilityStatistics();
  const prefersReducedMotion = useReducedMotion();

  if (isPending) return <ChartSkeleton />;

  if (isError) {
    return (
      <ErrorState
        title="Unable to load severity distribution"
        description="Vulnerability severity data could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  const distribution = data.severity_distribution;
  const segments = SEVERITY_ORDER.map((key) => ({
    key,
    label: SEVERITY_META[key].label,
    value: distribution[key],
    fill: SEVERITY_META[key].chartColor,
  })).filter((segment) => segment.value > 0);

  if (segments.length === 0) {
    return (
      <EmptyState
        icon={ShieldQuestion}
        title="No vulnerabilities recorded yet"
        description="Severity distribution will appear once scans discover vulnerabilities."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="mx-auto h-48 w-48 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={segments}
              dataKey="value"
              nameKey="label"
              innerRadius="62%"
              outerRadius="100%"
              paddingAngle={2}
              strokeWidth={0}
              // design_system.md §23 Chart Animation: 200–400ms initial
              // animation, disabled under prefers-reduced-motion.
              isAnimationActive={!prefersReducedMotion}
              animationDuration={300}
            />
            <Tooltip
              formatter={(value, name) => [formatCount(Number(value)), String(name)]}
              contentStyle={{
                background: "var(--popover)",
                color: "var(--popover-foreground)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
                boxShadow: "var(--shadow-md)",
                fontSize: "0.75rem",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <ul className="flex flex-1 flex-col gap-2">
        {SEVERITY_ORDER.map((key) => {
          const meta = SEVERITY_META[key];
          const value = distribution[key];
          return (
            <li key={key} className="flex items-center justify-between gap-3 text-sm">
              <span className="flex items-center gap-2 text-foreground">
                <span
                  className="size-2 shrink-0 rounded-full"
                  style={{ backgroundColor: meta.chartColor }}
                  aria-hidden="true"
                />
                {meta.label}
              </span>
              <span className="font-mono tabular-nums text-muted-foreground">
                {formatCount(value)}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
