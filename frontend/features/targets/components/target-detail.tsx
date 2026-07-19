"use client";

import { PlayCircle, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyableValue } from "@/components/shared/copyable-value";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { AssetList } from "@/features/assets/components/asset-list";
import { ScanList } from "@/features/scans/components/scan-list";
import { useCreateScan } from "@/features/scans/hooks/use-scans";
import { DeleteTargetDialog } from "@/features/targets/components/delete-target-dialog";
import { useTarget } from "@/features/targets/hooks/use-targets";
import { TARGET_TYPE_LABELS } from "@/features/targets/types/target";
import { VulnerabilityList } from "@/features/vulnerabilities/components/vulnerability-list";
import { formatDateTime } from "@/utils/format";

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground">{children}</div>
    </div>
  );
}

export function TargetDetail({ targetId }: { targetId: string }) {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { data: target, isPending, isError, refetch } = useTarget(targetId);
  const { mutate: createScan, isPending: isStartingScan } = useCreateScan();

  function handleStartScan() {
    if (isStartingScan) return;
    createScan(
      { target_id: targetId },
      {
        onSuccess: (scan) => {
          toast.success("Scan started");
          router.push(`/scans/${scan.scan_id}`);
        },
        onError: (error) => toast.error(error.message),
      }
    );
  }

  if (isPending) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Card>
          <CardContent className="flex flex-col gap-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isError || !target) {
    return (
      <div className="mx-auto flex max-w-[1600px] flex-col">
        <PageHeader title="Target" />
        <ErrorState
          title="Unable to load this target"
          description="The target record could not be retrieved."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
      <PageHeader
        title={target.target}
        description={TARGET_TYPE_LABELS[target.target_type]}
        actions={
          <div className="flex items-center gap-2">
            <Button onClick={handleStartScan} disabled={isStartingScan}>
              <PlayCircle className="size-4" aria-hidden="true" />
              {isStartingScan ? "Starting scan…" : "Start Scan"}
            </Button>
            <Button variant="outline" onClick={() => setDeleteOpen(true)}>
              <Trash2 className="size-4" aria-hidden="true" />
              Delete
            </Button>
          </div>
        }
      />

      <Card>
        <CardContent className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <DetailField label="Target">
            <CopyableValue value={target.target} />
          </DetailField>
          <DetailField label="Type">{TARGET_TYPE_LABELS[target.target_type]}</DetailField>
          <DetailField label="Added">{formatDateTime(target.created_at)}</DetailField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scans</CardTitle>
        </CardHeader>
        <CardContent>
          <ScanList targetId={target.id} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Assets Discovered</CardTitle>
        </CardHeader>
        <CardContent>
          <AssetList targetId={target.id} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Vulnerabilities Found</CardTitle>
        </CardHeader>
        <CardContent>
          <VulnerabilityList targetId={target.id} />
        </CardContent>
      </Card>

      <DeleteTargetDialog
        target={target}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onDeleted={() => router.push("/targets")}
      />
    </div>
  );
}
