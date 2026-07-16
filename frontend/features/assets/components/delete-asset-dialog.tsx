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
import { useDeleteAsset } from "@/features/assets/hooks/use-assets";
import type { AssetResponse } from "@/features/assets/types/asset";

export function DeleteAssetDialog({
  asset,
  open,
  onOpenChange,
  onDeleted,
}: {
  asset: AssetResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called after a confirmed deletion — e.g. to navigate away from a detail page. */
  onDeleted?: () => void;
}) {
  const { mutate, isPending } = useDeleteAsset();

  function handleConfirm(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault(); // wait for server confirmation before closing
    if (isPending) return;

    mutate(asset.id, {
      onSuccess: () => {
        toast.success("Asset deleted");
        onOpenChange(false);
        onDeleted?.();
      },
      onError: (error) => {
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
          <AlertDialogTitle>Delete asset?</AlertDialogTitle>
          <AlertDialogDescription>
            This permanently removes the asset and its discovered network
            services. Scan findings referencing this asset are also removed.
            The underlying vulnerability catalog and generated reports are
            not affected. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="flex flex-col gap-1 rounded-md border border-border bg-muted/50 px-3 py-2">
          <span className="font-mono text-sm text-foreground">{asset.ipv4}</span>
          {asset.hostname && (
            <span className="text-xs text-muted-foreground">{asset.hostname}</span>
          )}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isPending}
            className="bg-destructive/10 text-destructive hover:bg-destructive/20"
          >
            {isPending ? "Deleting…" : "Delete Asset"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
