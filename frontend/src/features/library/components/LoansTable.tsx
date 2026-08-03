import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useLoans } from "../api/useLoans";
import { useReturnLoan } from "../api/useReturnLoan";
import type { Loan } from "../types";

interface LoansTableProps {
  page: number;
  pageSize: number;
  ordering?: string;
  borrowerType?: "student" | "staff";
  returned?: boolean;
  search?: string;
  onPageChange: (page: number) => void;
}

export function LoansTable({
  page,
  pageSize,
  ordering,
  borrowerType,
  returned,
  search,
  onPageChange,
}: LoansTableProps) {
  const query = useLoans({ page, pageSize, ordering, borrowerType, returned, search });
  const { mutate: returnLoan, isPending, variables: returningId } = useReturnLoan();

  const columns = [
    { key: "copy", header: "Copy", render: (row: Loan) => row.copy },
    { key: "borrower", header: "Borrower", render: (row: Loan) => `${row.borrower_type} · ${row.borrower_id}` },
    { key: "due_date", header: "Due date", render: (row: Loan) => row.due_date },
    {
      key: "actions",
      header: "",
      render: (row: Loan) =>
        row.returned_at === null && (
          <Button
            variant="outline"
            disabled={isPending && returningId === row.id}
            onClick={() => returnLoan(row.id)}
          >
            Return
          </Button>
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
          emptyMessage="No loans match these filters."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
