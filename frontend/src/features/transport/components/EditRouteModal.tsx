import { useState } from "react";

import { ApiError } from "@/shared/lib/api";
import { Modal } from "@/shared/components/Modal";

import { useUpdateRoute } from "../api/useUpdateRoute";
import type { RouteFormValues } from "../forms/route.schema";
import type { Route } from "../types";
import { RouteForm } from "./RouteForm";

interface EditRouteModalProps {
  /** `null` when no row's "Edit" button has been clicked yet — the modal
   * stays closed in that state. */
  route: Route | null;
  onClose: () => void;
}

export function EditRouteModal({ route, onClose }: EditRouteModalProps) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { mutateAsync, isPending } = useUpdateRoute();

  async function handleSubmit(values: RouteFormValues) {
    if (!route) return;
    setErrorMessage(null);
    try {
      await mutateAsync({ id: route.id, input: values });
      onClose();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "Could not update this route.");
    }
  }

  return (
    <Modal open={route !== null} onClose={onClose} title="Edit route">
      <RouteForm
        onSubmit={handleSubmit}
        defaultValues={route ? { name: route.name, vehicle: route.vehicle } : undefined}
        isSubmitting={isPending}
        errorMessage={errorMessage}
      />
    </Modal>
  );
}
