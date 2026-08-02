import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { StatTile } from "@/shared/components/StatTile";
import { Table } from "@/shared/components/Table";

import { useStudentDashboard } from "../api/useStudentDashboard";
import { formatCurrency, formatPercent } from "../format";
import type { StudentDashboard as StudentDashboardData } from "../types";

type StudentDocument = StudentDashboardData["documents"][number];

const columns = [
  {
    key: "name",
    header: "Document",
    render: (row: StudentDocument) => row.minio_object_key.split("/").pop() ?? row.minio_object_key,
  },
];

export function StudentDashboard() {
  const query = useStudentDashboard();

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <StatTile label="My attendance rate" value={formatPercent(data.attendance_rate)} />
            <StatTile label="Fee balance" value={formatCurrency(data.balance)} />
          </div>
          <h2 className="text-lg font-semibold text-text">My documents</h2>
          <Table
            columns={columns}
            rows={data.documents}
            getRowKey={(row) => row.id}
            emptyMessage="No documents on file yet."
          />
        </div>
      )}
    </QueryBoundary>
  );
}
