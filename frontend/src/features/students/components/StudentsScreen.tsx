import { useState } from "react";

import { Button } from "@/shared/components/Button";

import { CreateStudentModal } from "./CreateStudentModal";
import { StudentsTable } from "./StudentsTable";

export function StudentsScreen() {
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Students</h2>
        <Button onClick={() => setModalOpen(true)}>Add student</Button>
      </div>
      <StudentsTable page={page} onPageChange={setPage} />
      <CreateStudentModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
