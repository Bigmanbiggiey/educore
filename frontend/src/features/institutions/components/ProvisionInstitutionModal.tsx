import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useProvisionInstitution } from "../api/useProvisionInstitution";
import type { ProvisionInstitutionFormValues } from "../forms/provision-institution.schema";
import { ProvisionInstitutionForm } from "./ProvisionInstitutionForm";

interface ProvisionInstitutionModalProps {
  open: boolean;
  onClose: () => void;
}

export function ProvisionInstitutionModal({ open, onClose }: ProvisionInstitutionModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useProvisionInstitution();

  async function handleSubmit(values: ProvisionInstitutionFormValues) {
    setErrorMessage(null);
    try {
      await mutateAsync(values);
      onClose();
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError ? error.message : "Could not provision this institution.",
      );
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Provision institution">
      <ProvisionInstitutionForm
        onSubmit={handleSubmit}
        isSubmitting={isPending}
        errorMessage={errorMessage}
      />
    </Modal>
  );
}
