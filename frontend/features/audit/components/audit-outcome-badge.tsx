import type { AuditOutcome } from "@/features/audit/types/audit";
import { cn } from "@/lib/utils";

/**
 * Mirrors ScanStatusBadge's exact visual structure (dot + label, operational
 * status colors) — the same established idiom applied to a different
 * two-value backend enum, not a new visual language.
 */
const OUTCOME_META: Record<AuditOutcome, { label: string; textClass: string; bgClass: string }> = {
  SUCCESS: { label: "Success", textClass: "text-success", bgClass: "bg-success-bg" },
  FAILURE: { label: "Failure", textClass: "text-destructive", bgClass: "bg-destructive-bg" },
};

export function AuditOutcomeBadge({
  outcome,
  className,
}: {
  outcome: AuditOutcome;
  className?: string;
}) {
  const meta = OUTCOME_META[outcome];

  return (
    <span
      className={cn(
        "inline-flex h-[26px] items-center gap-1.5 rounded-full px-2.5 text-xs font-medium",
        meta.bgClass,
        meta.textClass,
        className
      )}
    >
      <span className="size-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
      {meta.label}
    </span>
  );
}
