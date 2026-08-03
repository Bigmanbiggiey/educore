import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedRooms } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface RoomsListParams {
  page: number;
  pageSize: number;
  ordering?: string;
}

export function useRooms({ page, pageSize, ordering }: RoomsListParams) {
  return useQuery({
    queryKey: ["hostel", "rooms", { page, pageSize, ordering }],
    queryFn: () =>
      api.get<PaginatedRooms>(`/rooms/${buildQueryString({ page, page_size: pageSize, ordering })}`),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
