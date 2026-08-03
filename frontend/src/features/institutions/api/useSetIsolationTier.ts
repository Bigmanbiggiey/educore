import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Institution, SetIsolationTierInput } from "../types";

export function useSetIsolationTier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ institutionId, input }: { institutionId: string; input: SetIsolationTierInput }) =>
      api.post<Institution>(`/platform/institutions/${institutionId}/set-isolation-tier/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["institutions"] });
    },
  });
}
