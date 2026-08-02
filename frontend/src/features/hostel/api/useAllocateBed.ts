import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { AllocateBedInput, BedAllocation } from "../types";

export function useAllocateBed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AllocateBedInput) => api.post<BedAllocation>("/bed-allocations/", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["hostel"] });
    },
  });
}
