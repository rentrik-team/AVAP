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
import type { AssetDetailResponse } from "@/features/assets/types/asset";
import { formatDateTime, formatRelativeTime } from "@/utils/format";

const MAX_INLINE_SERVICES = 3;

function ServiceBadges({ services }: { services: AssetDetailResponse["services"] }) {
  if (services.length === 0) {
    return <span className="text-sm text-muted-foreground">No open services</span>;
  }
  const shown = services.slice(0, MAX_INLINE_SERVICES);
  const overflow = services.length - shown.length;
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {shown.map((service) => (
        <span
          key={service.id}
          className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 font-mono text-xs font-medium text-foreground"
        >
          {service.port}/{service.protocol.toUpperCase()} {service.service_name}
        </span>
      ))}
      {overflow > 0 && (
        <span className="text-xs text-muted-foreground">+{overflow} more</span>
      )}
    </div>
  );
}

export function AssetTable({
  assets,
  onDeleteRequest,
}: {
  assets: AssetDetailResponse[];
  onDeleteRequest: (asset: AssetDetailResponse) => void;
}) {
  return (
    <div className="hidden overflow-hidden rounded-xl border border-border md:block">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Asset</TableHead>
            <TableHead>Operating System</TableHead>
            <TableHead>Services</TableHead>
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
                <ServiceBadges services={asset.services} />
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
