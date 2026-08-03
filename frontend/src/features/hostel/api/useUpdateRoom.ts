import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Room } from "../types";

interface UpdateRoomInput {
  room_number: string;
  capacity: number;
}

export function useUpdateRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateRoomInput }) =>
      api.patch<Room>(`/rooms/${id}/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["hostel"] });
    },
  });
}
