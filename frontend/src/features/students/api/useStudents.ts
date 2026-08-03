import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedStudents } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface StudentsListParams {
  page: number;
  pageSize: number;
  ordering?: string;
  search?: string;
}

export function useStudents({ page, pageSize, ordering, search }: StudentsListParams) {
  return useQuery({
    queryKey: ["students", "list", { page, pageSize, ordering, search }],
    queryFn: () =>
      api.get<PaginatedStudents>(
        `/students/${buildQueryString({ page, page_size: pageSize, ordering, search })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
