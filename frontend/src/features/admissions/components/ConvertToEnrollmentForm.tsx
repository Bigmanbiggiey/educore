import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import {
  convertToEnrollmentSchema,
  type ConvertToEnrollmentFormValues,
} from "../forms/convert-to-enrollment.schema";

interface ConvertToEnrollmentFormProps {
  onSubmit: (values: ConvertToEnrollmentFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `ConvertToEnrollmentModal` (which owns the mutation +
 * open/close state) so it can be tested with a plain mocked `onSubmit`, same
 * split every other feature's form/modal pair established. */
export function ConvertToEnrollmentForm({
  onSubmit,
  isSubmitting,
  errorMessage,
}: ConvertToEnrollmentFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ConvertToEnrollmentFormValues>({ resolver: zodResolver(convertToEnrollmentSchema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField
        label="Admission number"
        error={errors.admission_number?.message}
        {...register("admission_number")}
      />
      <TextField
        label="Class grade ID"
        error={errors.class_grade_id?.message}
        {...register("class_grade_id")}
      />
      <TextField label="Term ID" error={errors.term_id?.message} {...register("term_id")} />
      <TextField
        label="Stream ID (optional)"
        error={errors.stream_id?.message}
        {...register("stream_id")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Converting…" : "Convert to enrollment"}
      </Button>
    </form>
  );
}
