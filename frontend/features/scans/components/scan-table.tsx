"use client";

import Link from "next/link";

import { ScanStatusBadge } from "@/components/shared/scan-status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { CopyableValue } from "@/components/shared/copyable-value";
import { ScanRowActions } from "@/features/scans/components/scan-row-actions";
import type { ScanResponse } from "@/features/scans/types/scan";
import type { TargetResponse } from "@/features/targets/types/target";
import { formatDateTime, formatDuration, formatLabel, formatRelativeTime } from "@/utils/format";

export function ScanTable({
  scans,
  targetsById,
  onDeleteRequest,
}: {
  scans: ScanResponse[];
  targetsById: Map<string, TargetResponse>;
  onDeleteRequest: (scan: ScanResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Scan</TableHead>
            <TableHead>Target</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead className="w-12 text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scans.map((scan) => {
            const target = targetsById.get(scan.target_id);
            return (
              <TableRow key={scan.scan_id} className="h-13">
                <TableCell>
                  <Link
                    href={`/scans/${scan.scan_id}`}
                    className="text-sm font-medium text-foreground hover:text-primary hover:underline"
                  >
                    {formatLabel(scan.scan_type)} Scan
                  </Link>
                </TableCell>
                <TableCell>
                  {target ? (
                    <CopyableValue value={target.target} className="text-sm" />
                  ) : (
                    <span className="font-mono text-xs text-muted-foreground">
                      {scan.target_id}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  <ScanStatusBadge status={scan.status} />
                </TableCell>
                <TableCell>
                  {scan.started_at ? (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="text-sm text-muted-foreground">
                          {formatRelativeTime(scan.started_at)}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>{formatDateTime(scan.started_at)}</TooltipContent>
                    </Tooltip>
                  ) : (
                    <span className="text-sm text-muted-foreground">Not started</span>
                  )}
                </TableCell>
                <TableCell>
                  <span className="font-mono text-sm text-muted-foreground">
                    {formatDuration(scan.execution_duration)}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <ScanRowActions scan={scan} onDeleteRequest={onDeleteRequest} />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
