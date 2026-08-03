import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useUpdateClinicVisit } from "../api/useUpdateClinicVisit";
import type { RecordVisitFormValues } from "../forms/record-visit.schema";
import type { ClinicVisit } from "../types";
import { VisitForm } from "./VisitForm";

interface EditVisitModalProps {
  /** `null` when no row's "Edit" button has been clicked yet — the modal
   * stays closed in that state. */
  visit: ClinicVisit | null;
  onClose: () => void;
}

export function EditVisitModal({ visit, onClose }: EditVisitModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useUpdateClinicVisit();

  async function handleSubmit(values: RecordVisitFormValues) {
    if (!visit) return;
    setErrorMessage(null);
    try {
      await mutateAsync({ id: visit.id, input: values });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not update this visit.");
    }
  }

  return (
    <Modal open={visit !== null} onClose={onClose} title="Edit visit">
      <VisitForm
        onSubmit={handleSubmit}
        defaultValues={
          visit
            ? {
                student_id: visit.student_id,
                visit_date: visit.visit_date,
                treated_by_id: visit.treated_by_id,
                notes: visit.notes ?? "",
              }
            : undefined
        }
        submitLabel="Save changes"
        submittingLabel="Saving…"
        isSubmitting={isPending}
        errorMessage={errorMessage}
      />
    </Modal>
  );
}
