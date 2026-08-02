import { useState } from "react";

import { InvoicesTable } from "./InvoicesTable";
import { RecordPaymentModal } from "./RecordPaymentModal";

export function FinanceScreen() {
  const [page, setPage] = useState(1);
  const [invoiceId, setInvoiceId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Invoices</h2>
      <InvoicesTable page={page} onPageChange={setPage} onRecordPayment={setInvoiceId} />
      <RecordPaymentModal invoiceId={invoiceId} onClose={() => setInvoiceId(null)} />
    </div>
  );
}
