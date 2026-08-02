import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedStudents } from "../types";

const PAGE_SIZE = 25;

export function useStudents(page: number) {
  return useQuery({
    queryKey: ["students", "list", { page }],
    queryFn: () =>
      api.get<PaginatedStudents>(`/students/?page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
