import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useCreateStudent } from "../api/useCreateStudent";
import type { CreateStudentFormValues } from "../forms/create-student.schema";
import { CreateStudentForm } from "./CreateStudentForm";

interface CreateStudentModalProps {
  open: boolean;
  onClose: () => void;
}

export function CreateStudentModal({ open, onClose }: CreateStudentModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useCreateStudent();

  async function handleSubmit(values: CreateStudentFormValues) {
    setErrorMessage(null);
    try {
      await mutateAsync({ ...values, gender: values.gender || undefined });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not add this student.");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add student">
      <CreateStudentForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
