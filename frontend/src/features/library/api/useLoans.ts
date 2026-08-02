import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedLoans } from "../types";

const PAGE_SIZE = 25;

export function useLoans(page: number) {
  return useQuery({
    queryKey: ["library", "loans", { page }],
    queryFn: () =>
      api.get<PaginatedLoans>(`/loans/?returned=false&page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
