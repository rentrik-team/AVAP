import { ScanDetail } from "@/features/scans/components/scan-detail";

export default async function ScanDetailPage({
  params,
}: {
  params: Promise<{ scanId: string }>;
}) {
  const { scanId } = await params;
  return <ScanDetail scanId={scanId} />;
}
