import { PageHeader } from "@/components/shared/page-header";
import { VulnerabilityList } from "@/features/vulnerabilities/components/vulnerability-list";

export default function VulnerabilitiesPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Vulnerabilities"
        description="The normalized vulnerability catalog across all scans. AI-inferred entries are labelled — they are educated inferences from service banners, not scanner-confirmed results."
      />
      <VulnerabilityList />
    </div>
  );
}
