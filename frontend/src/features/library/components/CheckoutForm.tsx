import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { checkoutSchema, type CheckoutFormValues } from "../forms/checkout.schema";

interface CheckoutFormProps {
  onSubmit: (values: CheckoutFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

const BORROWER_TYPE_OPTIONS = [
  { value: "student", label: "Student" },
  { value: "staff", label: "Staff" },
];

/** Kept separate from `CheckoutModal` (which owns the mutation + open/close
 * state) so it can be tested with a plain mocked `onSubmit`, same split
 * `features/students`' `CreateStudentForm`/`CreateStudentModal` established. */
export function CheckoutForm({ onSubmit, isSubmitting, errorMessage }: CheckoutFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CheckoutFormValues>({ resolver: zodResolver(checkoutSchema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Copy ID" error={errors.copy?.message} {...register("copy")} />
      <Select
        label="Borrower type"
        options={BORROWER_TYPE_OPTIONS}
        error={errors.borrower_type?.message}
        {...register("borrower_type")}
      />
      <TextField label="Borrower ID" error={errors.borrower_id?.message} {...register("borrower_id")} />
      <TextField
        label="Due date"
        type="date"
        error={errors.due_date?.message}
        {...register("due_date")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Checking out…" : "Check out"}
      </Button>
    </form>
  );
}
