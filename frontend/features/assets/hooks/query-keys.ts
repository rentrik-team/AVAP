import type { AssetListFilters } from "@/features/assets/types/asset";

/** Deterministic query key factory for the Assets feature. */
export const assetKeys = {
  all: ["assets"] as const,
  lists: () => [...assetKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number } & AssetListFilters) =>
    [...assetKeys.lists(), params] as const,
  details: () => [...assetKeys.all, "detail"] as const,
  detail: (id: string) => [...assetKeys.details(), id] as const,
};
