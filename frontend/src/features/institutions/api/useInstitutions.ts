import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedInstitutions } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface InstitutionsListParams {
  page: number;
  pageSize: number;
}

export function useInstitutions({ page, pageSize }: InstitutionsListParams) {
  return useQuery({
    queryKey: ["institutions", "list", { page, pageSize }],
    queryFn: () =>
      api.get<PaginatedInstitutions>(
        `/platform/institutions/${buildQueryString({ page, page_size: pageSize })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
