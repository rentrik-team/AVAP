/** Deterministic query key factory for the Scans feature. */
export const scanKeys = {
  all: ["scans"] as const,
  lists: () => [...scanKeys.all, "list"] as const,
  list: (params: { skip: number; limit: number }) =>
    [...scanKeys.lists(), params] as const,
  details: () => [...scanKeys.all, "detail"] as const,
  detail: (id: string) => [...scanKeys.details(), id] as const,
  status: (id: string) => [...scanKeys.all, "status", id] as const,
};
