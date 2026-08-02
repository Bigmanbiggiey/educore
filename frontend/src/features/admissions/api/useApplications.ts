import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedApplications } from "../types";

const PAGE_SIZE = 25;

export function useApplications(page: number) {
  return useQuery({
    queryKey: ["admissions", "applications", { page }],
    queryFn: () =>
      api.get<PaginatedApplications>(`/applications/?page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
