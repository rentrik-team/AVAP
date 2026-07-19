import { TargetDetail } from "@/features/targets/components/target-detail";

export default async function TargetDetailPage({
  params,
}: {
  params: Promise<{ targetId: string }>;
}) {
  const { targetId } = await params;
  return <TargetDetail targetId={targetId} />;
}
