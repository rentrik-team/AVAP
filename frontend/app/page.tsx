import { ChartCard } from "@/components/shared/chart-card";
import { FadeIn } from "@/components/shared/fade-in";
import { PageHeader } from "@/components/shared/page-header";
import { AiRemediationCoverage } from "@/features/dashboard/components/ai-remediation-coverage";
import { CoreMetricCards } from "@/features/dashboard/components/core-metric-cards";
import { RecentlyDiscoveredAssets } from "@/features/dashboard/components/recently-discovered-assets";
import { RecentReports } from "@/features/dashboard/components/recent-reports";
import { RiskHero } from "@/features/dashboard/components/risk-hero";
import { ScanActivity } from "@/features/dashboard/components/scan-activity";
import { SeverityDistributionChart } from "@/features/dashboard/components/severity-distribution-chart";
import { TopRiskAssets } from "@/features/dashboard/components/top-risk-assets";
import { TopRiskVulnerabilities } from "@/features/dashboard/components/top-risk-vulnerabilities";

// design_system.md §32 Dashboard Layout — 12-column grid: Overall Risk
// Summary 8 cols / Severity Distribution 4 cols; Top Risk Assets 6 /
// Top Vulnerabilities 6; Scan Activity 8 / AI Coverage 4; Recent Reports
// 12 (full width). "Recently Discovered Assets" (the /dashboard/assets
// endpoint) isn't enumerated in that example grid — it's paired 6/6 with
// Recent Reports here as the doc's own "Recent Reports / Activity" closing
// section, per §32's explicit allowance to adapt the layout to real data
// density rather than rigidly forcing an unlisted endpoint into a 12-col
// slot that doesn't fit it.
export default function DashboardPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Overview"
        description="Real-time security posture across your environment."
      />

      <div className="flex flex-col gap-8">
        <FadeIn className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <RiskHero />
          <ChartCard
            title="Severity Distribution"
            description="Vulnerability catalog by severity rating"
            className="lg:col-span-4"
          >
            <SeverityDistributionChart />
          </ChartCard>
        </FadeIn>

        <FadeIn delay={0.05}>
          <CoreMetricCards />
        </FadeIn>

        <FadeIn delay={0.1} className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <ChartCard
            title="Top Risk Assets"
            description="Ranked by current risk score"
            className="lg:col-span-6"
          >
            <TopRiskAssets />
          </ChartCard>
          <ChartCard
            title="Top Risk Vulnerabilities"
            description="Ranked by current risk score"
            className="lg:col-span-6"
          >
            <TopRiskVulnerabilities />
          </ChartCard>
        </FadeIn>

        <FadeIn delay={0.15} className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <ChartCard
            title="Scan Activity"
            description="Recent scan execution and success rate"
            className="lg:col-span-8"
          >
            <ScanActivity />
          </ChartCard>
          <ChartCard
            title="AI Remediation Coverage"
            description="Recommendation availability across eligible findings"
            className="lg:col-span-4"
          >
            <AiRemediationCoverage />
          </ChartCard>
        </FadeIn>

        <FadeIn delay={0.2} className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <ChartCard
            title="Recent Reports"
            description="Latest generated assessment reports"
            className="lg:col-span-6"
          >
            <RecentReports />
          </ChartCard>
          <ChartCard
            title="Recently Discovered Assets"
            description="Newest assets found across scans"
            className="lg:col-span-6"
          >
            <RecentlyDiscoveredAssets />
          </ChartCard>
        </FadeIn>
      </div>
    </div>
  );
}
