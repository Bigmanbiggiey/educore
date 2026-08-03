import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { components } from "@/shared/lib/api-types";
import type { BedAllocation } from "../types";

type PaginatedBedAllocations = components["schemas"]["PaginatedBedAllocationList"];

/** The current occupants of a room/term — lets the warden actually see
 * (and free up) individual beds, not just the aggregate counts
 * `useRoomOccupancy` returns. */
export function useRoomAllocations(roomId: string | null, termId: string | null | undefined) {
  return useQuery({
    queryKey: ["hostel", "allocations", roomId, termId],
    queryFn: () =>
      api.get<PaginatedBedAllocations>(
        `/bed-allocations/${buildQueryString({ room: roomId ?? undefined, term_id: termId ?? undefined, page_size: 100 })}`,
      ),
    enabled: roomId !== null && !!termId,
  });
}

export type { BedAllocation };
