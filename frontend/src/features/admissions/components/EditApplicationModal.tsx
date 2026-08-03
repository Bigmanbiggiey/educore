import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useUpdateApplication } from "../api/useUpdateApplication";
import type { ApplicationDetailsFormValues } from "../forms/application-details.schema";
import { applicantDetailsRecord, type Application } from "../types";
import { ApplicationDetailsForm } from "./ApplicationDetailsForm";

interface EditApplicationModalProps {
  /** `null` when no row's "Edit" button has been clicked yet — the modal
   * stays closed in that state. */
  application: Application | null;
  onClose: () => void;
}

export function EditApplicationModal({ application, onClose }: EditApplicationModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useUpdateApplication();

  async function handleSubmit(values: ApplicationDetailsFormValues) {
    if (!application) return;
    setErrorMessage(null);
    try {
      // Merge onto the existing `applicant_details` rather than replacing
      // it outright — it's an unstructured blob that may hold other keys
      // (DOB, guardian contact) this form never touches, and a bare
      // `{ first_name, last_name }` PATCH would silently drop them.
      const { first_name, last_name, term_applying_for_id } = values;
      await mutateAsync({
        id: application.id,
        input: {
          applicant_details: { ...applicantDetailsRecord(application), first_name, last_name },
          term_applying_for_id,
        },
      });
      onClose();
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError ? error.message : "Could not update this application.",
      );
    }
  }

  const details = application ? applicantDetailsRecord(application) : {};

  return (
    <Modal open={application !== null} onClose={onClose} title="Edit application">
      <ApplicationDetailsForm
        onSubmit={handleSubmit}
        defaultValues={
          application
            ? {
                first_name: typeof details.first_name === "string" ? details.first_name : "",
                last_name: typeof details.last_name === "string" ? details.last_name : "",
                term_applying_for_id: application.term_applying_for_id,
              }
            : undefined
        }
        isSubmitting={isPending}
        errorMessage={errorMessage}
      />
    </Modal>
  );
}
