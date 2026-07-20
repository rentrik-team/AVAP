import { PageHeader } from "@/components/shared/page-header";
import { RiskList } from "@/features/risk/components/risk-list";
import { RiskSummaryCard } from "@/features/risk/components/risk-summary-card";

export default function FindingsPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Findings"
        description="Deterministic, risk-scored findings calculated by AVAP's Risk Engine — filter by scope or level, and open a vulnerability finding to generate AI remediation guidance."
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
