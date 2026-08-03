import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import {
  applicationDetailsSchema,
  type ApplicationDetailsFormValues,
} from "../forms/application-details.schema";

interface ApplicationDetailsFormProps {
  onSubmit: (values: ApplicationDetailsFormValues) => Promise<void> | void;
  defaultValues?: Partial<ApplicationDetailsFormValues>;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Edits only the plain-writable parts of an `Application` — `stage`,
 * `stage_history`, and `offers` are read-only server-side (the lifecycle
 * moves only through Make Offer / Accept Offer / Convert to Enrollment),
 * so there's nothing for this form to touch there. */
export function ApplicationDetailsForm({
  onSubmit,
  defaultValues,
  isSubmitting,
  errorMessage,
}: ApplicationDetailsFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ApplicationDetailsFormValues>({
    resolver: zodResolver(applicationDetailsSchema),
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="First name" error={errors.first_name?.message} {...register("first_name")} />
      <TextField label="Last name" error={errors.last_name?.message} {...register("last_name")} />
      <TextField
        label="Term applying for ID"
        error={errors.term_applying_for_id?.message}
        {...register("term_applying_for_id")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
