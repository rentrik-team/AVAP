"use client";

import Link from "next/link";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { AssetRowActions } from "@/features/assets/components/asset-row-actions";
import type { AssetResponse } from "@/features/assets/types/asset";
import { formatDateTime, formatRelativeTime } from "@/utils/format";

export function AssetTable({
  assets,
  onDeleteRequest,
}: {
  assets: AssetResponse[];
  onDeleteRequest: (asset: AssetResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Asset</TableHead>
            <TableHead>Operating System</TableHead>
            <TableHead>Discovered</TableHead>
            <TableHead className="w-12 text-right">
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {assets.map((asset) => (
            <TableRow key={asset.id} className="h-13">
              <TableCell>
                <div className="flex flex-col">
                  <Link
                    href={`/assets/${asset.id}`}
                    className="font-mono text-sm font-medium text-foreground hover:text-primary hover:underline"
                  >
                    {asset.ipv4}
                  </Link>
                  {asset.hostname && (
                    <span className="truncate text-xs text-muted-foreground">
                      {asset.hostname}
                    </span>
                  )}
                </div>
              </TableCell>
              <TableCell>
                <span className="text-sm text-muted-foreground">
                  {asset.operating_system ?? "—"}
                </span>
              </TableCell>
              <TableCell>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="text-sm text-muted-foreground">
                      {formatRelativeTime(asset.created_at)}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>{formatDateTime(asset.created_at)}</TooltipContent>
                </Tooltip>
              </TableCell>
              <TableCell className="text-right">
                <AssetRowActions asset={asset} onDeleteRequest={onDeleteRequest} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
