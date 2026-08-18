import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import {
  INVITABLE_ROLE_OPTIONS,
  inviteMemberSchema,
  type InviteMemberFormValues,
} from "../forms/invite-member.schema";

interface InviteMemberFormProps {
  onSubmit: (values: InviteMemberFormValues) => Promise<void> | void;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `InviteMemberModal` (which owns the mutation +
 * open/close state) so it can be tested with a plain mocked `onSubmit`,
 * same split `ProvisionInstitutionForm`/`ProvisionInstitutionModal`
 * established. */
export function InviteMemberForm({ onSubmit, isSubmitting, errorMessage }: InviteMemberFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<InviteMemberFormValues>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: { role_name: INVITABLE_ROLE_OPTIONS[0].value },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField
        label="Email"
        type="email"
        error={errors.email?.message}
        {...register("email")}
      />
      <TextField
        label="Phone (optional)"
        error={errors.phone?.message}
        {...register("phone")}
      />
      <Select
        label="Role"
        error={errors.role_name?.message}
        options={[...INVITABLE_ROLE_OPTIONS]}
        {...register("role_name")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Inviting…" : "Invite member"}
      </Button>
    </form>
  );
}
