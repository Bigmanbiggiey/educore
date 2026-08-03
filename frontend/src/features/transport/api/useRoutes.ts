import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedRoutes } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface RoutesListParams {
  page: number;
  pageSize: number;
  ordering?: string;
}

export function useRoutes({ page, pageSize, ordering }: RoutesListParams) {
  return useQuery({
    queryKey: ["transport", "routes", { page, pageSize, ordering }],
    queryFn: () =>
      api.get<PaginatedRoutes>(`/routes/${buildQueryString({ page, page_size: pageSize, ordering })}`),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
