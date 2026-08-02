import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import { allocateBedSchema, type AllocateBedFormValues } from "../forms/allocate-bed.schema";

interface AllocateBedFormProps {
  onSubmit: (values: AllocateBedFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `AllocateBedModal` (which owns the mutation +
 * open/close state) so it can be tested with a plain mocked `onSubmit`, same
 * split `features/students`' `CreateStudentForm`/`CreateStudentModal` established. */
export function AllocateBedForm({ onSubmit, isSubmitting, errorMessage }: AllocateBedFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AllocateBedFormValues>({ resolver: zodResolver(allocateBedSchema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Student ID" error={errors.student_id?.message} {...register("student_id")} />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Allocating…" : "Allocate bed"}
      </Button>
    </form>
  );
}
