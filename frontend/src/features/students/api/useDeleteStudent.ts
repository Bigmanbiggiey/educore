import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

export function useDeleteStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (studentId: string) => api.delete<void>(`/students/${studentId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}
