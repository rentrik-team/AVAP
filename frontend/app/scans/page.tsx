import { PageHeader } from "@/components/shared/page-header";
import { ScanList } from "@/features/scans/components/scan-list";

export default function ScansPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Scans"
        description="Review scan jobs and their execution lifecycle. Start a new scan from a target's actions menu."
      />
      <ScanList />
    </div>
  );
}
