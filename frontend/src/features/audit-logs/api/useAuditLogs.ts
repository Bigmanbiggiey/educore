import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";
import { buildQueryString } from "@/shared/utils/buildQueryString";

import type { PaginatedAuditLogs } from "../types";

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50];

interface AuditLogsListParams {
  page: number;
  pageSize: number;
  institution?: string;
  actor?: string;
  action?: string;
}

export function useAuditLogs({ page, pageSize, institution, actor, action }: AuditLogsListParams) {
  return useQuery({
    queryKey: ["audit-logs", "list", { page, pageSize, institution, actor, action }],
    queryFn: () =>
      api.get<PaginatedAuditLogs>(
        `/platform/audit-logs/${buildQueryString({
          page,
          page_size: pageSize,
          institution,
          actor,
          action,
        })}`,
      ),
  });
}

export { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS };
