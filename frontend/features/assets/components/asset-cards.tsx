"use client";

import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { AssetRowActions } from "@/features/assets/components/asset-row-actions";
import type { AssetResponse } from "@/features/assets/types/asset";
import { formatRelativeTime } from "@/utils/format";

/** Mobile transformation of the asset table — design_system.md §41. */
export function AssetCards({
  assets,
  onDeleteRequest,
}: {
  assets: AssetResponse[];
  onDeleteRequest: (asset: AssetResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {assets.map((asset) => (
        <Card key={asset.id}>
          <CardContent className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 flex-col gap-1">
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
              <span className="text-xs text-muted-foreground">
                {asset.operating_system ?? "Operating system unknown"} ·{" "}
                {formatRelativeTime(asset.created_at)}
              </span>
            </div>
            <AssetRowActions asset={asset} onDeleteRequest={onDeleteRequest} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
