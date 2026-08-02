import { useState } from "react";

import { Modal } from "@/shared/components/Modal";
import { ApiError } from "@/shared/lib/api";

import { useRecordPayment } from "../api/useRecordPayment";
import type { RecordPaymentFormValues } from "../forms/record-payment.schema";
import { RecordPaymentForm } from "./RecordPaymentForm";

interface RecordPaymentModalProps {
  /** `null` when no row's "Record payment" button has been clicked yet —
   * the modal stays closed in that state. */
  invoiceId: string | null;
  onClose: () => void;
}

export function RecordPaymentModal({ invoiceId, onClose }: RecordPaymentModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useRecordPayment();

  async function handleSubmit(values: RecordPaymentFormValues) {
    if (!invoiceId) return;
    setErrorMessage(null);
    try {
      await mutateAsync({
        invoice: invoiceId,
        amount: values.amount,
        method: values.method,
        reference: values.reference,
        paid_at: new Date(values.paid_at).toISOString(),
      });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not record this payment.");
    }
  }

  return (
    <Modal open={invoiceId !== null} onClose={onClose} title="Record payment">
      <RecordPaymentForm onSubmit={handleSubmit} isSubmitting={isPending} errorMessage={errorMessage} />
    </Modal>
  );
}
