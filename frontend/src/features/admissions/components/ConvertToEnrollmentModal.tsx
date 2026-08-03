import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useConvertToEnrollment } from "../api/useConvertToEnrollment";
import type { ConvertToEnrollmentFormValues } from "../forms/convert-to-enrollment.schema";
import { ConvertToEnrollmentForm } from "./ConvertToEnrollmentForm";

interface ConvertToEnrollmentModalProps {
  /** `null` when no row's "Convert to enrollment" button has been clicked
   * yet — the modal stays closed in that state. */
  applicationId: string | null;
  onClose: () => void;
}

export function ConvertToEnrollmentModal({ applicationId, onClose }: ConvertToEnrollmentModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useConvertToEnrollment();

  async function handleSubmit(values: ConvertToEnrollmentFormValues) {
    if (!applicationId) return;
    setErrorMessage(null);
    try {
      await mutateAsync({ applicationId, input: values });
      onClose();
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError ? error.message : "Could not convert this application.",
      );
    }
  }

  return (
    <Modal open={applicationId !== null} onClose={onClose} title="Convert to enrollment">
      <ConvertToEnrollmentForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
