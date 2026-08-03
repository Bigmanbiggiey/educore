import { Badge } from "@/shared/components/Badge";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useAuditLogs } from "../api/useAuditLogs";
import type { AuditLog } from "../types";

interface AuditLogsTableProps {
  page: number;
  pageSize: number;
  institution?: string;
  actor?: string;
  action?: string;
  onPageChange: (page: number) => void;
}

export function AuditLogsTable({
  page,
  pageSize,
  institution,
  actor,
  action,
  onPageChange,
}: AuditLogsTableProps) {
  const query = useAuditLogs({ page, pageSize, institution, actor, action });

  const columns = [
    { key: "action", header: "Action", render: (row: AuditLog) => row.action },
    { key: "actor", header: "Actor", render: (row: AuditLog) => row.actor ?? "system" },
    {
      key: "institution",
      header: "Institution",
      render: (row: AuditLog) => row.institution ?? "—",
    },
    {
      key: "acting_as_admin",
      header: "Break-glass",
      render: (row: AuditLog) =>
        row.acting_as_admin && <Badge tone="warning">acting as admin</Badge>,
    },
    { key: "created_at", header: "When", render: (row: AuditLog) => row.created_at },
  ];

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <Table
          columns={columns}
          rows={data.results}
          getRowKey={(row) => row.id}
          emptyMessage="No audit log entries match these filters."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
