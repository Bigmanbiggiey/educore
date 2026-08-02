import { useState } from "react";

import { Button } from "@/shared/components/Button";

import { RecordVisitModal } from "./RecordVisitModal";
import { VisitsTable } from "./VisitsTable";

export function ClinicScreen() {
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Clinic visits</h2>
        <Button onClick={() => setModalOpen(true)}>Record visit</Button>
      </div>
      <VisitsTable page={page} onPageChange={setPage} />
      <RecordVisitModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
