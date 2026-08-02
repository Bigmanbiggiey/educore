import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import { recordVisitSchema, type RecordVisitFormValues } from "../forms/record-visit.schema";

interface RecordVisitFormProps {
  onSubmit: (values: RecordVisitFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `RecordVisitModal` (which owns the mutation +
 * open/close state) so it can be tested with a plain mocked `onSubmit`, same
 * split `features/students`' `CreateStudentForm`/`CreateStudentModal` established. */
export function RecordVisitForm({ onSubmit, isSubmitting, errorMessage }: RecordVisitFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecordVisitFormValues>({ resolver: zodResolver(recordVisitSchema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Student ID" error={errors.student_id?.message} {...register("student_id")} />
      <TextField
        label="Visit date"
        type="date"
        error={errors.visit_date?.message}
        {...register("visit_date")}
      />
      <TextField
        label="Treating nurse's staff ID"
        error={errors.treated_by_id?.message}
        {...register("treated_by_id")}
      />
      <TextField label="Notes" error={errors.notes?.message} {...register("notes")} />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Recording…" : "Record visit"}
      </Button>
    </form>
  );
}
