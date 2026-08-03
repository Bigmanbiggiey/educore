import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import { routeSchema, type RouteFormValues } from "../forms/route.schema";

interface RouteFormProps {
  onSubmit: (values: RouteFormValues) => Promise<void> | void;
  defaultValues?: Partial<RouteFormValues>;
  submitLabel?: string;
  submittingLabel?: string;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `EditRouteModal` (which owns the mutation +
 * open/close state) so it can be tested with a plain mocked `onSubmit`,
 * same split every other feature's form/modal pair established. Serves
 * both create and edit — `defaultValues` is the only difference. */
export function RouteForm({
  onSubmit,
  defaultValues,
  submitLabel = "Save changes",
  submittingLabel = "Saving…",
  isSubmitting,
  errorMessage,
}: RouteFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RouteFormValues>({ resolver: zodResolver(routeSchema), defaultValues });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Route name" error={errors.name?.message} {...register("name")} />
      <TextField label="Vehicle ID" error={errors.vehicle?.message} {...register("vehicle")} />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? submittingLabel : submitLabel}
      </Button>
    </form>
  );
}
