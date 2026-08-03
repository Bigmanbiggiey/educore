import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { Application, PaginatedApplications } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface ApplicationsListParams {
  page: number;
  pageSize: number;
  ordering?: string;
  stage?: Application["stage"];
}

export function useApplications({ page, pageSize, ordering, stage }: ApplicationsListParams) {
  return useQuery({
    queryKey: ["admissions", "applications", { page, pageSize, ordering, stage }],
    queryFn: () =>
      api.get<PaginatedApplications>(
        `/applications/${buildQueryString({ page, page_size: pageSize, ordering, stage })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
