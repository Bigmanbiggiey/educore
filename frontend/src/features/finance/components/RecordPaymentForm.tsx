import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { recordPaymentSchema, type RecordPaymentFormValues } from "../forms/record-payment.schema";

interface RecordPaymentFormProps {
  onSubmit: (values: RecordPaymentFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

const METHOD_OPTIONS = [
  { value: "cash", label: "Cash" },
  { value: "bank", label: "Bank" },
  { value: "mpesa", label: "M-Pesa" },
];

export function RecordPaymentForm({ onSubmit, isSubmitting, errorMessage }: RecordPaymentFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecordPaymentFormValues>({
    resolver: zodResolver(recordPaymentSchema),
    defaultValues: { method: "cash" },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Amount" inputMode="decimal" error={errors.amount?.message} {...register("amount")} />
      <Select
        label="Method"
        options={METHOD_OPTIONS}
        error={errors.method?.message}
        {...register("method")}
      />
      <TextField label="Reference" error={errors.reference?.message} {...register("reference")} />
      <TextField
        label="Paid at"
        type="datetime-local"
        error={errors.paid_at?.message}
        {...register("paid_at")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Recording…" : "Record payment"}
      </Button>
    </form>
  );
}
