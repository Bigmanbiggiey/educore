import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { Invoice, PaginatedInvoices } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface InvoicesListParams {
  page: number;
  pageSize: number;
  ordering?: string;
  status?: Invoice["status"];
  student?: string;
}

export function useInvoices({ page, pageSize, ordering, status, student }: InvoicesListParams) {
  return useQuery({
    queryKey: ["finance", "invoices", { page, pageSize, ordering, status, student }],
    queryFn: () =>
      api.get<PaginatedInvoices>(
        `/invoices/${buildQueryString({ page, page_size: pageSize, ordering, status, student })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
