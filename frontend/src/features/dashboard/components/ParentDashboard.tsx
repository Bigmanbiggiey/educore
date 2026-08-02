import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useParentDashboard } from "../api/useParentDashboard";
import { formatCurrency } from "../format";
import type { ParentDashboard as ParentDashboardData } from "../types";

type Child = ParentDashboardData["children"][number];

const columns = [
  {
    key: "name",
    header: "Child",
    render: (row: Child) => `${row.first_name} ${row.last_name}`,
  },
  { key: "admission_number", header: "Admission No.", render: (row: Child) => row.admission_number },
  { key: "balance", header: "Fee balance", render: (row: Child) => formatCurrency(row.balance) },
];

export function ParentDashboard() {
  const query = useParentDashboard();

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-text">My children</h2>
          <Table
            columns={columns}
            rows={data.children}
            getRowKey={(row) => row.student_id}
            emptyMessage="No children linked to your account yet."
          />
        </div>
      )}
    </QueryBoundary>
  );
}
