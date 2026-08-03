import { Button } from "@/shared/components/Button";
import { Modal } from "@/shared/components/Modal";

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  isConfirming?: boolean;
  confirmLabel?: string;
}

/** The one "are you sure?" dialog every delete action across every feature
 * composes, same reasoning `Modal`/`Select` were built once in Stage 3
 * rather than per-feature. */
export function ConfirmModal({
  open,
  title,
  message,
  onConfirm,
  onCancel,
  isConfirming,
  confirmLabel = "Delete",
}: ConfirmModalProps) {
  return (
    <Modal open={open} onClose={onCancel} title={title}>
      <div className="flex flex-col gap-4">
        <p className="text-sm text-text">{message}</p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onCancel} disabled={isConfirming}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm} disabled={isConfirming}>
            {isConfirming ? "Deleting…" : confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
