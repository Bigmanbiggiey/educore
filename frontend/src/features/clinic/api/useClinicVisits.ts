import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedClinicVisits } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface ClinicVisitsListParams {
  page: number;
  pageSize: number;
  ordering?: string;
  studentId?: string;
  visitDate?: string;
}

export function useClinicVisits({
  page,
  pageSize,
  ordering,
  studentId,
  visitDate,
}: ClinicVisitsListParams) {
  return useQuery({
    queryKey: ["clinic", "visits", { page, pageSize, ordering, studentId, visitDate }],
    queryFn: () =>
      api.get<PaginatedClinicVisits>(
        `/clinic-visits/${buildQueryString({
          page,
          page_size: pageSize,
          ordering,
          student_id: studentId,
          visit_date: visitDate,
        })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
