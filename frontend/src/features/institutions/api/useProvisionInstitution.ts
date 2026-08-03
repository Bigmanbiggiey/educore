import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Institution, ProvisionInstitutionInput } from "../types";

export function useProvisionInstitution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProvisionInstitutionInput) =>
      api.post<Institution>("/platform/institutions/", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["institutions"] });
    },
  });
}
