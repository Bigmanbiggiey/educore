import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { PAGE_SIZE, useStudents } from "../api/useStudents";
import type { Student } from "../types";

const columns = [
  {
    key: "name",
    header: "Name",
    render: (row: Student) => `${row.first_name} ${row.last_name}`,
  },
  { key: "admission_number", header: "Admission No.", render: (row: Student) => row.admission_number },
  { key: "gender", header: "Gender", render: (row: Student) => row.gender || "—" },
];

interface StudentsTableProps {
  page: number;
  onPageChange: (page: number) => void;
}

export function StudentsTable({ page, onPageChange }: StudentsTableProps) {
  const query = useStudents(page);

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <Table
          columns={columns}
          rows={data.results}
          getRowKey={(row) => row.id}
          emptyMessage="No students enrolled yet."
          pagination={{ count: data.count, page, pageSize: PAGE_SIZE, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
