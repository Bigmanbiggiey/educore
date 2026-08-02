import { Badge } from "@/shared/components/Badge";
import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { PAGE_SIZE, useInvoices } from "../api/useInvoices";
import type { Invoice } from "../types";

const STATUS_TONE: Record<Invoice["status"], "neutral" | "success" | "warning" | "danger"> = {
  unpaid: "neutral",
  partial: "warning",
  paid: "success",
  overdue: "danger",
  cancelled: "neutral",
};

interface InvoicesTableProps {
  page: number;
  onPageChange: (page: number) => void;
  onRecordPayment: (invoiceId: string) => void;
}

export function InvoicesTable({ page, onPageChange, onRecordPayment }: InvoicesTableProps) {
  const query = useInvoices(page);

  const columns = [
    { key: "student", header: "Student", render: (row: Invoice) => row.student_id.slice(0, 8) },
    { key: "amount_due", header: "Amount due", render: (row: Invoice) => row.amount_due },
    {
      key: "status",
      header: "Status",
      render: (row: Invoice) => <Badge tone={STATUS_TONE[row.status]}>{row.status}</Badge>,
    },
    {
      key: "actions",
      header: "",
      render: (row: Invoice) =>
        row.status !== "paid" &&
        row.status !== "cancelled" && (
          <Button variant="outline" onClick={() => onRecordPayment(row.id)}>
            Record payment
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
          emptyMessage="No invoices yet."
          pagination={{ count: data.count, page, pageSize: PAGE_SIZE, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
