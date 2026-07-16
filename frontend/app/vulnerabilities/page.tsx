import { PageHeader } from "@/components/shared/page-header";
import { VulnerabilityList } from "@/features/vulnerabilities/components/vulnerability-list";

export default function VulnerabilitiesPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Vulnerabilities"
        description="Normalized vulnerability catalog discovered across assessed assets."
      />
      <VulnerabilityList />
    </div>
  );
}
