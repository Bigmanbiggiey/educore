import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useStudents } from "../api/useStudents";
import type { Student } from "../types";

interface StudentsTableProps {
  page: number;
  pageSize: number;
  ordering?: string;
  onPageChange: (page: number) => void;
  onEdit: (student: Student) => void;
  onDelete: (student: Student) => void;
}

export function StudentsTable({
  page,
  pageSize,
  ordering,
  onPageChange,
  onEdit,
  onDelete,
}: StudentsTableProps) {
  const query = useStudents({ page, pageSize, ordering });

  const columns = [
    {
      key: "name",
      header: "Name",
      render: (row: Student) => `${row.first_name} ${row.last_name}`,
    },
    { key: "admission_number", header: "Admission No.", render: (row: Student) => row.admission_number },
    { key: "gender", header: "Gender", render: (row: Student) => row.gender || "—" },
    {
      key: "actions",
      header: "",
      render: (row: Student) => (
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
          emptyMessage="No students enrolled yet."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
