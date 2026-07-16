import { ReportDetail } from "@/features/reports/components/report-detail";

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ reportId: string }>;
}) {
  const { reportId } = await params;
  return <ReportDetail reportId={reportId} />;
}
