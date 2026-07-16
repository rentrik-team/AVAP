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
import { useDeleteTarget } from "@/features/targets/hooks/use-targets";
import type { TargetResponse } from "@/features/targets/types/target";

export function DeleteTargetDialog({
  target,
  open,
  onOpenChange,
}: {
  target: TargetResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { mutate, isPending } = useDeleteTarget();

  function handleConfirm(event: React.MouseEvent<HTMLButtonElement>) {
    // AlertDialogAction closes on click by default (it's a DialogPrimitive.Close
    // under the hood) — suppress that so the dialog stays open, showing a
    // pending state, until the backend actually confirms the deletion.
    event.preventDefault();
    if (isPending) return;

    mutate(target.id, {
      onSuccess: () => {
        toast.success("Target deleted");
        onOpenChange(false);
      },
      onError: (error) => {
        toast.error(error.message);
        // Already gone server-side (e.g. deleted from another session) —
        // nothing left to confirm, so close rather than block on a retry.
        if (error.code === "NOT_FOUND") onOpenChange(false);
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
          <AlertDialogTitle>Delete target?</AlertDialogTitle>
          <AlertDialogDescription>
            This permanently removes the target. Per AVAP&apos;s data model,
            deleting a target also removes its associated scan history. This
            cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <p className="truncate rounded-md border border-border bg-muted/50 px-3 py-2 font-mono text-sm text-foreground">
          {target.target}
        </p>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isPending}
            className="bg-destructive/10 text-destructive hover:bg-destructive/20"
          >
            {isPending ? "Deleting…" : "Delete Target"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
