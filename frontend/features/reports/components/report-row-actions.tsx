"use client";

import { Download, MoreHorizontal, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useDownloadReport } from "@/features/reports/hooks/use-reports";
import { triggerBrowserDownload } from "@/features/reports/lib/download";
import type { ReportResponse } from "@/features/reports/types/report";

export function ReportRowActions({
  report,
  onDeleteRequest,
}: {
  report: ReportResponse;
  onDeleteRequest: (report: ReportResponse) => void;
}) {
  const { mutate, isPending } = useDownloadReport();

  function handleDownload() {
    if (isPending) return;
    mutate(report.id, {
      onSuccess: (blob) => triggerBrowserDownload(blob, `avap-report-${report.id}.pdf`),
      onError: (error) => toast.error(error.message),
    });
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label="Report actions">
          <MoreHorizontal className="size-4" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          disabled={isPending}
          onSelect={(event) => {
            event.preventDefault();
            handleDownload();
          }}
        >
          <Download className="size-4" aria-hidden="true" />
          {isPending ? "Downloading…" : "Download"}
        </DropdownMenuItem>
        <DropdownMenuItem
          variant="destructive"
          onSelect={(event) => {
            event.preventDefault();
            onDeleteRequest(report);
          }}
        >
          <Trash2 className="size-4" aria-hidden="true" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
