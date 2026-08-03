import { useState } from "react";

import { Button } from "@/shared/components/Button";
import { Select } from "@/shared/components/Select";

import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useLoans";
import { CheckoutModal } from "./CheckoutModal";
import { LoansTable } from "./LoansTable";

const BORROWER_TYPE_OPTIONS = [
  { value: "", label: "All borrowers" },
  { value: "student", label: "Students" },
  { value: "staff", label: "Staff" },
];

const LOAN_STATE_OPTIONS = [
  { value: "active", label: "Active loans" },
  { value: "returned", label: "Returned loans" },
  { value: "all", label: "All loans" },
];

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "due_date", label: "Due date (earliest first)" },
  { value: "-due_date", label: "Due date (latest first)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

function loanStateToReturned(state: string): boolean | undefined {
  if (state === "active") return false;
  if (state === "returned") return true;
  return undefined;
}

export function LibraryScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [borrowerType, setBorrowerType] = useState<"student" | "staff" | "">("");
  const [loanState, setLoanState] = useState("active");
  const [modalOpen, setModalOpen] = useState(false);

  function resetToFirstPage() {
    setPage(1);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Loans</h2>
        <Button onClick={() => setModalOpen(true)}>Check out</Button>
      </div>
      <div className="flex flex-wrap gap-4">
        <Select
          label="Loan state"
          name="loan-state"
          options={LOAN_STATE_OPTIONS}
          value={loanState}
          onChange={(event) => {
            setLoanState(event.target.value);
            resetToFirstPage();
          }}
        />
        <Select
          label="Borrower type"
          name="borrower-type-filter"
          options={BORROWER_TYPE_OPTIONS}
          value={borrowerType}
          onChange={(event) => {
            setBorrowerType(event.target.value as "student" | "staff" | "");
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
      <LoansTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        borrowerType={borrowerType || undefined}
        returned={loanStateToReturned(loanState)}
        onPageChange={setPage}
      />
      <CheckoutModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
