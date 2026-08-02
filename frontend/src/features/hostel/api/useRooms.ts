import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedRooms } from "../types";

const PAGE_SIZE = 25;

export function useRooms(page: number) {
  return useQuery({
    queryKey: ["hostel", "rooms", { page }],
    queryFn: () => api.get<PaginatedRooms>(`/rooms/?page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
