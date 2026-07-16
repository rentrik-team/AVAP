import { PageHeader } from "@/components/shared/page-header";
import { ReportList } from "@/features/reports/components/report-list";

export default function ReportsPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Reports"
        description="Immutable, generated assessment reports. Start a new report from a scan's detail page."
      />
      <ReportList />
    </div>
  );
}
