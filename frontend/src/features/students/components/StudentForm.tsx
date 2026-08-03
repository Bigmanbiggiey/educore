import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { createStudentSchema, type CreateStudentFormValues } from "../forms/create-student.schema";

interface StudentFormProps {
  onSubmit: (values: CreateStudentFormValues) => Promise<void> | void;
  defaultValues?: Partial<CreateStudentFormValues>;
  submitLabel?: string;
  submittingLabel?: string;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

const GENDER_OPTIONS = [
  { value: "", label: "Not specified" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
];

/** Kept separate from `CreateStudentModal`/`EditStudentModal` (which own
 * the mutation + open/close state) so it can be tested with a plain mocked
 * `onSubmit`, same split `features/auth`'s `LoginForm`/`LoginPage`
 * established. Serves both create and edit — `defaultValues` is the only
 * difference, threaded straight into `useForm`. */
export function StudentForm({
  onSubmit,
  defaultValues,
  submitLabel = "Add student",
  submittingLabel = "Adding…",
  isSubmitting,
  errorMessage,
}: StudentFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateStudentFormValues>({
    resolver: zodResolver(createStudentSchema),
    defaultValues,
  });

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
      <TextField label="First name" error={errors.first_name?.message} {...register("first_name")} />
      <TextField label="Last name" error={errors.last_name?.message} {...register("last_name")} />
      <TextField
        label="Date of birth"
        type="date"
        error={errors.date_of_birth?.message}
        {...register("date_of_birth")}
      />
      <Select
        label="Gender"
        options={GENDER_OPTIONS}
        error={errors.gender?.message}
        {...register("gender")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? submittingLabel : submitLabel}
      </Button>
    </form>
  );
}
