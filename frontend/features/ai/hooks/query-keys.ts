/** Deterministic query key factory for the AI feature. */
export const aiKeys = {
  all: ["ai"] as const,
  recommendations: () => [...aiKeys.all, "recommendation"] as const,
  recommendation: (assessmentId: string) =>
    [...aiKeys.recommendations(), assessmentId] as const,
};
