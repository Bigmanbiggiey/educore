import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useCheckoutLoan } from "../api/useCheckoutLoan";
import type { CheckoutFormValues } from "../forms/checkout.schema";
import { CheckoutForm } from "./CheckoutForm";

interface CheckoutModalProps {
  open: boolean;
  onClose: () => void;
}

export function CheckoutModal({ open, onClose }: CheckoutModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useCheckoutLoan();

  async function handleSubmit(values: CheckoutFormValues) {
    setErrorMessage(null);
    try {
      await mutateAsync(values);
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not check out this book.");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Check out">
      <CheckoutForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
