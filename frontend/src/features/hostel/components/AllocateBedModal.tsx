import { useState } from "react";

import { useCurrentTerm } from "@/features/academic-terms";
import { Modal } from "@/shared/components/Modal";
import { ApiError } from "@/shared/lib/api";

import { useAllocateBed } from "../api/useAllocateBed";
import type { AllocateBedFormValues } from "../forms/allocate-bed.schema";
import { AllocateBedForm } from "./AllocateBedForm";

interface AllocateBedModalProps {
  /** `null` when no row's "Allocate bed" button has been clicked yet —
   * the modal stays closed in that state. */
  roomId: string | null;
  onClose: () => void;
}

export function AllocateBedModal({ roomId, onClose }: AllocateBedModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { data: currentTerm } = useCurrentTerm();
  const { mutateAsync, isPending } = useAllocateBed();

  async function handleSubmit(values: AllocateBedFormValues) {
    if (!roomId) return;
    if (!currentTerm) {
      setErrorMessage("No current term is set up — cannot allocate a bed.");
      return;
    }
    setErrorMessage(null);
    try {
      await mutateAsync({ room: roomId, student_id: values.student_id, term_id: currentTerm.id });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not allocate this bed.");
    }
  }

  return (
    <Modal open={roomId !== null} onClose={onClose} title="Allocate bed">
      <AllocateBedForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
