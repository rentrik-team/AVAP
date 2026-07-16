import { PageHeader } from "@/components/shared/page-header";
import { RiskList } from "@/features/risk/components/risk-list";
import { RiskSummaryCard } from "@/features/risk/components/risk-summary-card";

export default function RiskPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Risk"
        description="Deterministic, explainable risk assessments calculated by AVAP's Risk Engine across vulnerabilities, assets, scans, and the overall platform."
      />

      <div className="flex flex-col gap-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <RiskSummaryCard />
        </div>

        <RiskList />
      </div>
    </div>
  );
}
