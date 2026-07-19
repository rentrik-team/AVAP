import type { ScanStatus } from "@/features/dashboard/types/dashboard";
import { cn } from "@/lib/utils";

const STATUS_META: Record<
  ScanStatus,
  { label: string; textClass: string; bgClass: string; pulse?: boolean }
> = {
  PENDING: {
    label: "Pending",
    textClass: "text-muted-foreground",
    bgClass: "bg-muted",
  },
  RUNNING: {
    label: "Running",
    textClass: "text-info",
    bgClass: "bg-info-bg",
    pulse: true,
  },
  COMPLETED: {
    label: "Completed",
    textClass: "text-success",
    bgClass: "bg-success-bg",
  },
  FAILED: {
    label: "Failed",
    textClass: "text-destructive",
    bgClass: "bg-destructive-bg",
  },
  CANCELLED: {
    label: "Cancelled",
    textClass: "text-muted-foreground",
    bgClass: "bg-muted",
  },
};

/** Scan lifecycle status — an operational signal, not a security severity. */
export function ScanStatusBadge({
  status,
  className,
}: {
  status: ScanStatus;
  className?: string;
}) {
  const meta = STATUS_META[status];

  return (
    <span
      className={cn(
        "inline-flex h-[26px] items-center gap-1.5 rounded-full px-2.5 text-xs font-medium",
        meta.bgClass,
        meta.textClass,
        className
      )}
    >
      <span
        className={cn(
          "size-1.5 shrink-0 rounded-full bg-current",
          meta.pulse && "animate-pulse motion-reduce:animate-none"
        )}
        aria-hidden="true"
      />
      {meta.label}
    </span>
  );
}
