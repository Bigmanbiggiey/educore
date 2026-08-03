import { useState } from "react";

import { Button } from "@/shared/components/Button";

import { DEFAULT_PAGE_SIZE } from "../api/useInstitutions";
import type { Institution } from "../types";
import { InstitutionsTable } from "./InstitutionsTable";
import { ManageInstitutionModal } from "./ManageInstitutionModal";
import { ProvisionInstitutionModal } from "./ProvisionInstitutionModal";

interface InstitutionsScreenProps {
  /** Starts a break-glass act-as session for this institution
   * (docs/permissions.md §7) — owned by whatever composes this screen,
   * since `features/*` may not import `app/`'s `useAuth` directly. */
  onActAs: (institution: Institution) => void;
}

export function InstitutionsScreen({ onActAs }: InstitutionsScreenProps) {
  const [page, setPage] = useState(1);
  const [provisionModalOpen, setProvisionModalOpen] = useState(false);
  const [managingInstitution, setManagingInstitution] = useState<Institution | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Institutions</h2>
        <Button onClick={() => setProvisionModalOpen(true)}>Provision institution</Button>
      </div>
      <InstitutionsTable
        page={page}
        pageSize={DEFAULT_PAGE_SIZE}
        onPageChange={setPage}
        onManage={setManagingInstitution}
        onActAs={onActAs}
      />
      <ProvisionInstitutionModal
        open={provisionModalOpen}
        onClose={() => setProvisionModalOpen(false)}
      />
      <ManageInstitutionModal
        institution={managingInstitution}
        onClose={() => setManagingInstitution(null)}
      />
    </div>
  );
}
