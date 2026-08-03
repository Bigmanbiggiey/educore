import { useMutation } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { AddCustomDomainInput, Domain } from "../types";

export function useAddCustomDomain() {
  return useMutation({
    mutationFn: ({ institutionId, input }: { institutionId: string; input: AddCustomDomainInput }) =>
      api.post<Domain>(`/platform/institutions/${institutionId}/domains/`, input),
  });
}
