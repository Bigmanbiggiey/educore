import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useClinicVisits } from "../api/useClinicVisits";
import type { ClinicVisit } from "../types";

interface VisitsTableProps {
  page: number;
  pageSize: number;
  ordering?: string;
  studentId?: string;
  visitDate?: string;
  search?: string;
  onPageChange: (page: number) => void;
  onEdit: (visit: ClinicVisit) => void;
  onDelete: (visit: ClinicVisit) => void;
}

export function VisitsTable({
  page,
  pageSize,
  ordering,
  studentId,
  visitDate,
  search,
  onPageChange,
  onEdit,
  onDelete,
}: VisitsTableProps) {
  const query = useClinicVisits({ page, pageSize, ordering, studentId, visitDate, search });

  const columns = [
    { key: "student", header: "Student", render: (row: ClinicVisit) => row.student_id },
    { key: "visit_date", header: "Visit date", render: (row: ClinicVisit) => row.visit_date },
    { key: "notes", header: "Notes", render: (row: ClinicVisit) => row.notes || "—" },
    {
      key: "actions",
      header: "",
      render: (row: ClinicVisit) => (
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => onEdit(row)}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => onDelete(row)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <Table
          columns={columns}
          rows={data.results}
          getRowKey={(row) => row.id}
          emptyMessage="No clinic visits match these filters."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
