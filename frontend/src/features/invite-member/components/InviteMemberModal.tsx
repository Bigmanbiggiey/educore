import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useInviteMember } from "../api/useInviteMember";
import type { InviteMemberFormValues } from "../forms/invite-member.schema";
import { InviteMemberForm } from "./InviteMemberForm";

interface InviteMemberModalProps {
  open: boolean;
  onClose: () => void;
}

export function InviteMemberModal({ open, onClose }: InviteMemberModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useInviteMember();

  async function handleSubmit(values: InviteMemberFormValues) {
    setErrorMessage(null);
    try {
      await mutateAsync(values);
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not invite this member.");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Invite member">
      <InviteMemberForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
