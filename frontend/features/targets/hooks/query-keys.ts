/** Deterministic query key factory for the Targets feature. */
export const targetKeys = {
  all: ["targets"] as const,
  lists: () => [...targetKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number }) =>
    [...targetKeys.lists(), params] as const,
  details: () => [...targetKeys.all, "detail"] as const,
  detail: (id: string) => [...targetKeys.details(), id] as const,
};
