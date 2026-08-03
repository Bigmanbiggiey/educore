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
}

export function useStudents({ page, pageSize, ordering }: StudentsListParams) {
  return useQuery({
    queryKey: ["students", "list", { page, pageSize, ordering }],
    queryFn: () =>
      api.get<PaginatedStudents>(
        `/students/${buildQueryString({ page, page_size: pageSize, ordering })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
