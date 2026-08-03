import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

export function useDeleteBedAllocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (allocationId: string) => api.delete<void>(`/bed-allocations/${allocationId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["hostel"] });
    },
  });
}
