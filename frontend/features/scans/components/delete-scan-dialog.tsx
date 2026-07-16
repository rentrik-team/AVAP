"use client";

import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useDeleteScan } from "@/features/scans/hooks/use-scans";
import type { ScanResponse } from "@/features/scans/types/scan";
import { formatLabel } from "@/utils/format";

export function DeleteScanDialog({
  scan,
  open,
  onOpenChange,
  onDeleted,
}: {
  scan: ScanResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called after a confirmed deletion — e.g. to navigate away from a detail page. */
  onDeleted?: () => void;
}) {
  const { mutate, isPending } = useDeleteScan();

  function handleConfirm(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault(); // wait for server confirmation before closing
    if (isPending) return;

    mutate(scan.scan_id, {
      onSuccess: () => {
        toast.success("Scan deleted");
        onOpenChange(false);
        onDeleted?.();
      },
      onError: (error) => {
        // Preserves the backend's RUNNING-scan protection rule exactly —
        // a race (scan started running after the menu disabled state was
        // rendered) still surfaces the real 409 rather than being masked.
        toast.error(error.message);
      },
    });
  }

  return (
    <AlertDialog
      open={open}
      onOpenChange={(next) => {
        if (!isPending) onOpenChange(next);
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete scan?</AlertDialogTitle>
          <AlertDialogDescription>
            This permanently removes the scan job and its associated
            findings. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <p className="rounded-md border border-border bg-muted/50 px-3 py-2 text-sm text-foreground">
          {formatLabel(scan.scan_type)} scan
        </p>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isPending}
            className="bg-destructive/10 text-destructive hover:bg-destructive/20"
          >
            {isPending ? "Deleting…" : "Delete Scan"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
