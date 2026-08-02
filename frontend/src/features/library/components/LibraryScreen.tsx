import { useState } from "react";

import { Button } from "@/shared/components/Button";

import { CheckoutModal } from "./CheckoutModal";
import { LoansTable } from "./LoansTable";

export function LibraryScreen() {
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Active loans</h2>
        <Button onClick={() => setModalOpen(true)}>Check out</Button>
      </div>
      <LoansTable page={page} onPageChange={setPage} />
      <CheckoutModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
