import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { ClinicVisit, RecordVisitInput } from "../types";

export function useUpdateClinicVisit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: RecordVisitInput }) =>
      api.patch<ClinicVisit>(`/clinic-visits/${id}/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["clinic"] });
    },
  });
}
