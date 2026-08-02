import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedRoutes } from "../types";

const PAGE_SIZE = 25;

export function useRoutes(page: number) {
  return useQuery({
    queryKey: ["transport", "routes", { page }],
    queryFn: () => api.get<PaginatedRoutes>(`/routes/?page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
