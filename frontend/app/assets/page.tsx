import { PageHeader } from "@/components/shared/page-header";
import { AssetList } from "@/features/assets/components/asset-list";

export default function AssetsPage() {
  return (
    <div className="mx-auto flex max-w-[1600px] flex-col">
      <PageHeader
        title="Assets"
        description="Infrastructure discovered by completed scans, with open network services and system context."
      />
      <AssetList />
    </div>
  );
}
