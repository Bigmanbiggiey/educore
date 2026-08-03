import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

export function useDeleteRoute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (routeId: string) => api.delete<void>(`/routes/${routeId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["transport"] });
    },
  });
}
