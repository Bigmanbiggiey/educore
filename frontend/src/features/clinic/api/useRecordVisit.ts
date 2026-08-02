import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { ClinicVisit, RecordVisitInput } from "../types";

export function useRecordVisit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RecordVisitInput) => api.post<ClinicVisit>("/clinic-visits/", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["clinic"] });
    },
  });
}
