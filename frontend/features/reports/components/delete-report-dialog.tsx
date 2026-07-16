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
import { useDeleteReport } from "@/features/reports/hooks/use-reports";
import type { ReportResponse } from "@/features/reports/types/report";
import { formatDateTime } from "@/utils/format";

export function DeleteReportDialog({
  report,
  open,
  onOpenChange,
  onDeleted,
}: {
  report: ReportResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeleted?: () => void;
}) {
  const { mutate, isPending } = useDeleteReport();

  function handleConfirm(event: React.MouseEvent<HTMLButtonElement>) {
    event.preventDefault(); // wait for server confirmation before closing
    if (isPending) return;

    mutate(report.id, {
      onSuccess: () => {
        toast.success("Report deleted");
        onOpenChange(false);
        onDeleted?.();
      },
      onError: (error) => toast.error(error.message),
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
          <AlertDialogTitle>Delete report?</AlertDialogTitle>
          <AlertDialogDescription>
            This permanently removes the report metadata and its stored PDF
            file. The underlying scan, risk assessment, and vulnerability
            data are not affected. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <p className="rounded-md border border-border bg-muted/50 px-3 py-2 text-sm text-foreground">
          {report.format} report generated {formatDateTime(report.generated_at)}
        </p>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isPending}
            className="bg-destructive/10 text-destructive hover:bg-destructive/20"
          >
            {isPending ? "Deleting…" : "Delete Report"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
