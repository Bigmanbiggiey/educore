import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useUpdateRoom } from "../api/useUpdateRoom";
import type { RoomFormValues } from "../forms/room.schema";
import type { Room } from "../types";
import { RoomForm } from "./RoomForm";

interface EditRoomModalProps {
  /** `null` when no row's "Edit" button has been clicked yet — the modal
   * stays closed in that state. */
  room: Room | null;
  onClose: () => void;
}

export function EditRoomModal({ room, onClose }: EditRoomModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useUpdateRoom();

  async function handleSubmit(values: RoomFormValues) {
    if (!room) return;
    setErrorMessage(null);
    try {
      await mutateAsync({
        id: room.id,
        input: { room_number: values.room_number, capacity: Number(values.capacity) },
      });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not update this room.");
    }
  }

  return (
    <Modal open={room !== null} onClose={onClose} title="Edit room">
      <RoomForm
        onSubmit={handleSubmit}
        defaultValues={
          room ? { room_number: room.room_number, capacity: String(room.capacity) } : undefined
        }
        isSubmitting={isPending}
        errorMessage={errorMessage}
      />
    </Modal>
  );
}
