"use client";

import { PlayCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
// Scan creation is Scans-feature business: this component only triggers it
// from the Targets list, carrying the target's own identifier forward — it
// never calls the Targets or Scans API directly itself.
import { useCreateScan } from "@/features/scans/hooks/use-scans";

/** Row action that starts a scan for a target and hands the operator off
 * to the new scan's detail page to observe its lifecycle. */
export function StartScanMenuItem({ targetId }: { targetId: string }) {
  const router = useRouter();
  const { mutate, isPending } = useCreateScan();

  function handleSelect(event: Event) {
    event.preventDefault(); // keep the menu item's own pending/disabled state authoritative
    if (isPending) return;

    mutate(
      { target_id: targetId },
      {
        onSuccess: (scan) => {
          toast.success("Scan started");
          router.push(`/scans/${scan.scan_id}`);
        },
        onError: (error) => {
          toast.error(error.message);
        },
      }
    );
  }

  return (
    <DropdownMenuItem onSelect={handleSelect} disabled={isPending}>
      <PlayCircle className="size-4" aria-hidden="true" />
      {isPending ? "Starting scan…" : "Start Scan"}
    </DropdownMenuItem>
  );
}
