import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useRecordVisit } from "../api/useRecordVisit";
import type { RecordVisitFormValues } from "../forms/record-visit.schema";
import { RecordVisitForm } from "./RecordVisitForm";

interface RecordVisitModalProps {
  open: boolean;
  onClose: () => void;
}

export function RecordVisitModal({ open, onClose }: RecordVisitModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useRecordVisit();

  async function handleSubmit(values: RecordVisitFormValues) {
    setErrorMessage(null);
    try {
      await mutateAsync(values);
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not record this visit.");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Record visit">
      <RecordVisitForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
