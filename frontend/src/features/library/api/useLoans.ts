import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedLoans } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface LoansListParams {
  page: number;
  pageSize: number;
  ordering?: string;
  borrowerType?: "student" | "staff";
  /** `undefined` shows every loan regardless of return state. */
  returned?: boolean;
}

export function useLoans({ page, pageSize, ordering, borrowerType, returned }: LoansListParams) {
  return useQuery({
    queryKey: ["library", "loans", { page, pageSize, ordering, borrowerType, returned }],
    queryFn: () =>
      api.get<PaginatedLoans>(
        `/loans/${buildQueryString({
          page,
          page_size: pageSize,
          ordering,
          borrower_type: borrowerType,
          returned,
        })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
