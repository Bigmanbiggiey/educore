import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/shared/components/Button";
import { TextField } from "@/shared/components/TextField";

import { roomSchema, type RoomFormValues } from "../forms/room.schema";

interface RoomFormProps {
  onSubmit: (values: RoomFormValues) => Promise<void> | void;
  defaultValues?: Partial<RoomFormValues>;
  submitLabel?: string;
  submittingLabel?: string;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

/** Kept separate from `EditRoomModal` (which owns the mutation +
 * open/close state) so it can be tested with a plain mocked `onSubmit`,
 * same split every other feature's form/modal pair established. Serves
 * both create and edit — `defaultValues` is the only difference. */
export function RoomForm({
  onSubmit,
  defaultValues,
  submitLabel = "Save changes",
  submittingLabel = "Saving…",
  isSubmitting,
  errorMessage,
}: RoomFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RoomFormValues>({ resolver: zodResolver(roomSchema), defaultValues });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      {errorMessage && (
        <p role="alert" className="rounded-input bg-danger-muted px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}
      <TextField label="Room number" error={errors.room_number?.message} {...register("room_number")} />
      <TextField
        label="Capacity"
        type="number"
        error={errors.capacity?.message}
        {...register("capacity")}
      />
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? submittingLabel : submitLabel}
      </Button>
    </form>
  );
}
