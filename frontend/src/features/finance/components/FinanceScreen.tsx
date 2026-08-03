import { useState } from "react";

import { ConfirmModal } from "@/shared/components/ConfirmModal";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { useDeleteInvoice } from "../api/useDeleteInvoice";
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useInvoices";
import type { Invoice } from "../types";
import { InvoicesTable } from "./InvoicesTable";
import { RecordPaymentModal } from "./RecordPaymentModal";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "unpaid", label: "Unpaid" },
  { value: "partial", label: "Partial" },
  { value: "paid", label: "Paid" },
  { value: "overdue", label: "Overdue" },
  { value: "cancelled", label: "Cancelled" },
];

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "amount_due", label: "Amount due (low to high)" },
  { value: "-amount_due", label: "Amount due (high to low)" },
  { value: "status", label: "Status (A–Z)" },
  { value: "-status", label: "Status (Z–A)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function FinanceScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [status, setStatus] = useState<Invoice["status"] | "">("");
  const [student, setStudent] = useState("");
  const [invoiceId, setInvoiceId] = useState<string | null>(null);
  const [deletingInvoice, setDeletingInvoice] = useState<Invoice | null>(null);

  const { mutate: deleteInvoice, isPending: isDeleting } = useDeleteInvoice();

  function resetToFirstPage() {
    setPage(1);
  }

  function handleConfirmDelete() {
    if (!deletingInvoice) return;
    deleteInvoice(deletingInvoice.id, { onSuccess: () => setDeletingInvoice(null) });
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Invoices</h2>
      <div className="flex flex-wrap gap-4">
        <Select
          label="Status"
          name="status-filter"
          options={STATUS_OPTIONS}
          value={status}
          onChange={(event) => {
            setStatus(event.target.value as Invoice["status"] | "");
            resetToFirstPage();
          }}
        />
        <TextField
          label="Student ID"
          name="student-filter"
          value={student}
          onChange={(event) => {
            setStudent(event.target.value);
            resetToFirstPage();
          }}
        />
        <Select
          label="Sort by"
          name="sort-by"
          options={SORT_OPTIONS}
          value={ordering}
          onChange={(event) => {
            setOrdering(event.target.value);
            resetToFirstPage();
          }}
        />
        <Select
          label="Page size"
          name="page-size"
          options={PAGE_SIZE_SELECT_OPTIONS}
          value={String(pageSize)}
          onChange={(event) => {
            setPageSize(Number(event.target.value));
            resetToFirstPage();
          }}
        />
      </div>
      <InvoicesTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        status={status || undefined}
        student={student || undefined}
        onPageChange={setPage}
        onRecordPayment={setInvoiceId}
        onDelete={setDeletingInvoice}
      />
      <RecordPaymentModal invoiceId={invoiceId} onClose={() => setInvoiceId(null)} />
      <ConfirmModal
        open={deletingInvoice !== null}
        title="Delete invoice"
        message="Delete this invoice? This cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingInvoice(null)}
        isConfirming={isDeleting}
      />
    </div>
  );
}
