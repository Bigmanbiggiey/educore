import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import {
  CURRICULUM_TYPE_OPTIONS,
  provisionInstitutionSchema,
  type ProvisionInstitutionFormValues,
} from "../forms/provision-institution.schema";

interface ProvisionInstitutionFormProps {
  onSubmit: (values: ProvisionInstitutionFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `ProvisionInstitutionModal` (which owns the mutation
 * + open/close state) so it can be tested with a plain mocked `onSubmit`,
 * same split every other feature's form/modal pair established. */
export function ProvisionInstitutionForm({
  onSubmit,
  isSubmitting,
  errorMessage,
}: ProvisionInstitutionFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProvisionInstitutionFormValues>({
    resolver: zodResolver(provisionInstitutionSchema),
    defaultValues: { curriculum_types: [] },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Institution name" error={errors.name?.message} {...register("name")} />
      <TextField
        label="Slug"
        error={errors.slug?.message}
        {...register("slug")}
      />
      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium text-text">Curricula</legend>
        {CURRICULUM_TYPE_OPTIONS.map((option) => (
          <label key={option.value} className="flex items-center gap-2 text-sm text-text">
            <input type="checkbox" value={option.value} {...register("curriculum_types")} />
            {option.label}
          </label>
        ))}
        {errors.curriculum_types && (
          <p role="alert" className="text-sm text-danger">
            {errors.curriculum_types.message}
          </p>
        )}
      </fieldset>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Provisioning…" : "Provision institution"}
      </Button>
    </form>
  );
}
