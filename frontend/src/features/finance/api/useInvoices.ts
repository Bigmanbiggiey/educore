import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedInvoices } from "../types";

const PAGE_SIZE = 25;

export function useInvoices(page: number) {
  return useQuery({
    queryKey: ["finance", "invoices", { page }],
    queryFn: () => api.get<PaginatedInvoices>(`/invoices/?page=${page}&page_size=${PAGE_SIZE}`),
  });
}

export { PAGE_SIZE };
