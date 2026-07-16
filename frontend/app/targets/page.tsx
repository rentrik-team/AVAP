import { PageHeader } from "@/components/shared/page-header";
import { CreateTargetDialog } from "@/features/targets/components/create-target-dialog";
import { TargetList } from "@/features/targets/components/target-list";

export default function TargetsPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Targets"
        description="Register and manage the IPv4 addresses, CIDR ranges, and hostnames validated for assessment."
        actions={<CreateTargetDialog />}
      />
      <TargetList />
    </div>
  );
}
