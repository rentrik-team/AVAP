"use client";

import { Badge } from "@/components/ui/badge";
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
import { TargetRowActions } from "@/features/targets/components/target-row-actions";
import { TARGET_TYPE_LABELS, type TargetResponse } from "@/features/targets/types/target";
import { formatDateTime, formatRelativeTime } from "@/utils/format";

export function TargetTable({
  targets,
  onDeleteRequest,
}: {
  targets: TargetResponse[];
  onDeleteRequest: (target: TargetResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Target</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-12 text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {targets.map((target) => (
            <TableRow key={target.id} className="h-13">
              <TableCell>
                <CopyableValue value={target.target} className="text-sm" />
              </TableCell>
              <TableCell>
                <Badge variant="outline">{TARGET_TYPE_LABELS[target.target_type]}</Badge>
              </TableCell>
              <TableCell>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="text-sm text-muted-foreground">
                      {formatRelativeTime(target.created_at)}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>{formatDateTime(target.created_at)}</TooltipContent>
                </Tooltip>
              </TableCell>
              <TableCell className="text-right">
                <TargetRowActions target={target} onDeleteRequest={onDeleteRequest} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
