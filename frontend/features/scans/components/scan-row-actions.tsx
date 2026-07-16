"use client";

import { MoreHorizontal, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { ScanResponse } from "@/features/scans/types/scan";

export function ScanRowActions({
  scan,
  onDeleteRequest,
}: {
  scan: ScanResponse;
  onDeleteRequest: (scan: ScanResponse) => void;
}) {
  const isRunning = scan.status === "RUNNING";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label="Scan actions">
          <MoreHorizontal className="size-4" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {isRunning ? (
          <Tooltip>
            <TooltipTrigger asChild>
              {/* A disabled DropdownMenuItem still needs to accept the
                  Tooltip trigger's ref/props via a wrapping span, since
                  Radix disables pointer events on data-disabled items. */}
              <span>
                <DropdownMenuItem disabled variant="destructive">
                  <Trash2 className="size-4" aria-hidden="true" />
                  Delete
                </DropdownMenuItem>
              </span>
            </TooltipTrigger>
            <TooltipContent>Cannot delete a running scan</TooltipContent>
          </Tooltip>
        ) : (
          <DropdownMenuItem
            variant="destructive"
            onSelect={(event) => {
              event.preventDefault();
              onDeleteRequest(scan);
            }}
          >
            <Trash2 className="size-4" aria-hidden="true" />
            Delete
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
