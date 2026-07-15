import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/utils";

export function BrandMark({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <div className="flex items-center gap-2.5 overflow-hidden">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <ShieldCheck className="size-4.5" aria-hidden="true" />
      </span>
      <span
        className={cn(
          "flex flex-col leading-tight transition-opacity",
          collapsed && "w-0 opacity-0"
        )}
      >
        <span className="text-sm font-semibold tracking-tight whitespace-nowrap">
          AVAP
        </span>
        <span className="text-[11px] whitespace-nowrap text-muted-foreground">
          Vulnerability Assessment
        </span>
      </span>
    </div>
  );
}
