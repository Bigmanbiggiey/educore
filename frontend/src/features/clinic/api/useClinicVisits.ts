import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedClinicVisits } from "../types";

const PAGE_SIZE = 25;

export function useClinicVisits(page: number) {
  return useQuery({
    queryKey: ["clinic", "visits", { page }],
    queryFn: () =>
      api.get<PaginatedClinicVisits>(`/clinic-visits/?page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
