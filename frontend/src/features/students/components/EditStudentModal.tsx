import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useUpdateStudent } from "../api/useUpdateStudent";
import type { CreateStudentFormValues } from "../forms/create-student.schema";
import type { Student } from "../types";
import { StudentForm } from "./StudentForm";

interface EditStudentModalProps {
  /** `null` when no row's "Edit" button has been clicked yet — the modal
   * stays closed in that state. */
  student: Student | null;
  onClose: () => void;
}

export function EditStudentModal({ student, onClose }: EditStudentModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useUpdateStudent();

  async function handleSubmit(values: CreateStudentFormValues) {
    if (!student) return;
    setErrorMessage(null);
    try {
      await mutateAsync({
        id: student.id,
        input: { ...values, gender: values.gender || undefined },
      });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not update this student.");
    }
  }

  return (
    <Modal open={student !== null} onClose={onClose} title="Edit student">
      <StudentForm
        onSubmit={handleSubmit}
        defaultValues={
          student
            ? {
                admission_number: student.admission_number,
                first_name: student.first_name,
                last_name: student.last_name,
                date_of_birth: student.date_of_birth ?? "",
                gender: student.gender ?? "",
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
