import { AssetDetail } from "@/features/assets/components/asset-detail";

export default async function AssetDetailPage({
  params,
}: {
  params: Promise<{ assetId: string }>;
}) {
  const { assetId } = await params;
  return <AssetDetail assetId={assetId} />;
}
