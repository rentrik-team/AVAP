"use client";

import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyableValue } from "@/components/shared/copyable-value";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { DeleteAssetDialog } from "@/features/assets/components/delete-asset-dialog";
import { ServiceList } from "@/features/assets/components/service-list";
import { useAsset } from "@/features/assets/hooks/use-assets";
import { formatDateTime } from "@/utils/format";

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  );
}

export function AssetDetail({ assetId }: { assetId: string }) {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { data: asset, isPending, isError, refetch } = useAsset(assetId);

  if (isPending) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Card>
          <CardContent className="flex flex-col gap-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError || !asset) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col">
        <PageHeader title="Asset" />
        <ErrorState
          title="Unable to load this asset"
          description="The asset record could not be retrieved."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
      <PageHeader
        title={asset.ipv4}
        description={asset.hostname ?? undefined}
        actions={
          <Button variant="outline" onClick={() => setDeleteOpen(true)}>
            <Trash2 className="size-4" aria-hidden="true" />
            Delete
          </Button>
        }
      />

      <Card>
        <CardContent className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <DetailField label="IPv4 address">
            <CopyableValue value={asset.ipv4} />
          </DetailField>
          <DetailField label="Hostname">
            {asset.hostname ? <CopyableValue value={asset.hostname} /> : "—"}
          </DetailField>
          <DetailField label="Operating system">
            {asset.operating_system ?? "—"}
          </DetailField>
          <DetailField label="Discovered">{formatDateTime(asset.created_at)}</DetailField>
          <DetailField label="Last updated">{formatDateTime(asset.updated_at)}</DetailField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Network Services</CardTitle>
        </CardHeader>
        <CardContent>
          <ServiceList services={asset.services} />
        </CardContent>
      </Card>

      <DeleteAssetDialog
        asset={asset}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onDeleted={() => router.push("/assets")}
      />
    </div>
  );
}
