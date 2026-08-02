import { useState } from "react";

import { ApplicationsTable } from "./ApplicationsTable";

export function AdmissionsScreen() {
  const [page, setPage] = useState(1);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Applications</h2>
      <ApplicationsTable page={page} onPageChange={setPage} />
    </div>
  );
}
