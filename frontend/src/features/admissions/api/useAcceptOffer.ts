import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Application } from "../types";

export function useAcceptOffer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (applicationId: string) =>
      api.post<Application>(`/applications/${applicationId}/accept-offer/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admissions"] });
    },
  });
}
