import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { PAGE_SIZE, useClinicVisits } from "../api/useClinicVisits";
import type { ClinicVisit } from "../types";

const columns = [
  { key: "student", header: "Student", render: (row: ClinicVisit) => row.student_id },
  { key: "visit_date", header: "Visit date", render: (row: ClinicVisit) => row.visit_date },
  { key: "notes", header: "Notes", render: (row: ClinicVisit) => row.notes || "—" },
];

interface VisitsTableProps {
  page: number;
  onPageChange: (page: number) => void;
}

export function VisitsTable({ page, onPageChange }: VisitsTableProps) {
  const query = useClinicVisits(page);

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <Table
          columns={columns}
          rows={data.results}
          getRowKey={(row) => row.id}
          emptyMessage="No clinic visits recorded yet."
          pagination={{ count: data.count, page, pageSize: PAGE_SIZE, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
