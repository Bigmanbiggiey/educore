import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

export function useDeleteRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roomId: string) => api.delete<void>(`/rooms/${roomId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["hostel"] });
    },
  });
}
