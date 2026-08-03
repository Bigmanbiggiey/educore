import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

export function useDeleteClinicVisit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (visitId: string) => api.delete<void>(`/clinic-visits/${visitId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["clinic"] });
    },
  });
}
