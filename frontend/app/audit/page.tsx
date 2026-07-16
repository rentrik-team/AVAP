import { PageHeader } from "@/components/shared/page-header";
import { AuditList } from "@/features/audit/components/audit-list";

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<{ scan_id?: string }>;
}) {
  const { scan_id } = await searchParams;

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Audit Events"
        description="Immutable, chronological record of significant platform actions."
      />
      <AuditList initialScanId={scan_id} />
    </div>
  );
}
