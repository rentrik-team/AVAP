"use client";

import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { AssetRowActions } from "@/features/assets/components/asset-row-actions";
import type { AssetDetailResponse } from "@/features/assets/types/asset";
import { formatRelativeTime } from "@/utils/format";

const MAX_INLINE_SERVICES = 3;

/** Mobile transformation of the asset table — design_system.md §41. */
export function AssetCards({
  assets,
  onDeleteRequest,
}: {
  assets: AssetDetailResponse[];
  onDeleteRequest: (asset: AssetDetailResponse) => void;
}) {
  return (
    <div className="flex flex-col gap-3 md:hidden">
      {assets.map((asset) => {
        const shownServices = asset.services.slice(0, MAX_INLINE_SERVICES);
        const overflow = asset.services.length - shownServices.length;
        return (
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
                {asset.services.length > 0 && (
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    {shownServices.map((service) => (
                      <span
                        key={service.id}
                        className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 font-mono text-xs font-medium text-foreground"
                      >
                        {service.port}/{service.protocol.toUpperCase()}
                      </span>
                    ))}
                    {overflow > 0 && (
                      <span className="text-xs text-muted-foreground">
                        +{overflow} more
                      </span>
                    )}
                  </div>
                )}
              </div>
              <AssetRowActions asset={asset} onDeleteRequest={onDeleteRequest} />
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
