"use client";

import { Crosshair } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ListRowsSkeleton } from "@/components/shared/skeletons";
import { CreateTargetDialog } from "@/features/targets/components/create-target-dialog";
import { DeleteTargetDialog } from "@/features/targets/components/delete-target-dialog";
import { TargetCards } from "@/features/targets/components/target-cards";
import { TargetTable } from "@/features/targets/components/target-table";
import { useTargets } from "@/features/targets/hooks/use-targets";
import type { TargetResponse } from "@/features/targets/types/target";
import { formatCount } from "@/utils/format";

const PAGE_SIZE = 50;

export function TargetList() {
  const [skip, setSkip] = useState(0);
  const [targetPendingDelete, setTargetPendingDelete] = useState<TargetResponse | null>(
    null
  );
  const { data, isPending, isError, refetch } = useTargets({
    skip,
    limit: PAGE_SIZE,
  });

  if (isPending) {
    return <ListRowsSkeleton rows={6} />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load targets"
        description="Target inventory could not be retrieved."
        onRetry={() => refetch()}
      />
    );
  }

  if (data.targets.length === 0) {
    return (
      <EmptyState
        icon={Crosshair}
        title="No targets have been added yet"
        description="Add an IPv4 address, CIDR range, or hostname to begin assessing it."
        action={<CreateTargetDialog />}
      />
    );
  }

  const rangeStart = skip + 1;
  const rangeEnd = Math.min(skip + PAGE_SIZE, data.total);

  return (
    <div className="flex flex-col gap-4">
      <TargetTable targets={data.targets} onDeleteRequest={setTargetPendingDelete} />
      <TargetCards targets={data.targets} onDeleteRequest={setTargetPendingDelete} />

      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          Showing {formatCount(rangeStart)}–{formatCount(rangeEnd)} of{" "}
          {formatCount(data.total)}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSkip((prev) => Math.max(prev - PAGE_SIZE, 0))}
            disabled={skip === 0}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSkip((prev) => prev + PAGE_SIZE)}
            disabled={skip + PAGE_SIZE >= data.total}
          >
            Next
          </Button>
        </div>
      </div>

      {targetPendingDelete && (
        <DeleteTargetDialog
          target={targetPendingDelete}
          open
          onOpenChange={(next) => {
            if (!next) setTargetPendingDelete(null);
          }}
        />
      )}
    </div>
  );
}
