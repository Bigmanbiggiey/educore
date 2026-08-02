import type { components } from "@/shared/lib/api-types";

export type Loan = components["schemas"]["Loan"];
export type PaginatedLoans = components["schemas"]["PaginatedLoanList"];
export type Copy = components["schemas"]["Copy"];
export type PaginatedCopies = components["schemas"]["PaginatedCopyList"];

// See features/students/types.ts's CreateStudentInput for why this isn't
// just `Loan` — the generated schema doubles as the read shape too.
export interface CheckoutInput {
  copy: string;
  borrower_type: "student" | "staff";
  borrower_id: string;
  due_date: string;
}
