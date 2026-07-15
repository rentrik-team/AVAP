import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  context,
  icon: Icon,
  className,
}: {
  label: string;
  value: string;
  context?: string;
  icon?: LucideIcon;
  className?: string;
}) {
  return (
    <Card className={cn("rounded-xl", className)}>
      <CardContent className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-sm text-muted-foreground">{label}</span>
          <span className="font-mono text-2xl font-semibold tabular-nums text-foreground">
            {value}
          </span>
          {context && (
            <span className="text-xs text-muted-foreground">{context}</span>
          )}
        </div>
        {Icon && (
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Icon className="size-4.5" aria-hidden="true" />
          </span>
        )}
      </CardContent>
    </Card>
  );
}
