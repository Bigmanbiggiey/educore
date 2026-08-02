import type { components } from "@/shared/lib/api-types";

export type Invoice = components["schemas"]["Invoice"];
export type PaginatedInvoices = components["schemas"]["PaginatedInvoiceList"];

// See features/students/types.ts's CreateStudentInput for why this isn't
// just `Payment` — the generated schema doubles as the read shape too.
export interface RecordPaymentInput {
  invoice: string;
  amount: string;
  method: "mpesa" | "cash" | "bank";
  reference?: string;
  paid_at: string;
}
