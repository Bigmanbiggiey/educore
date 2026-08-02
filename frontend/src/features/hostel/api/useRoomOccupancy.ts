import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { RoomOccupancy } from "../types";

export function useRoomOccupancy(roomId: string | null, termId: string | null | undefined) {
  return useQuery({
    queryKey: ["hostel", "occupancy", roomId, termId],
    queryFn: () => api.get<RoomOccupancy>(`/rooms/${roomId}/occupancy/?term_id=${termId}`),
    enabled: roomId !== null && !!termId,
  });
}
