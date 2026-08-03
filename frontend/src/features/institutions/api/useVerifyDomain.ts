import { useMutation } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Domain, VerifyDomainInput } from "../types";

export function useVerifyDomain() {
  return useMutation({
    mutationFn: ({ domainId, input }: { domainId: string; input: VerifyDomainInput }) =>
      api.post<Domain>(`/platform/domains/${domainId}/verify/`, input),
  });
}
