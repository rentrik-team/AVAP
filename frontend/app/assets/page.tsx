import { PageHeader } from "@/components/shared/page-header";
import { AssetList } from "@/features/assets/components/asset-list";

export default function AssetsPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Assets"
        description="Every host discovered across all scans, with its open network services. Drill into an asset for ports, protocols, products, and versions."
      />
      <AssetList />
    </div>
  );
}
