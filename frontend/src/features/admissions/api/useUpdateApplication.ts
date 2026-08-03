import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Application } from "../types";

interface UpdateApplicationInput {
  applicant_details: Record<string, unknown>;
  term_applying_for_id: string;
}

export function useUpdateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateApplicationInput }) =>
      api.patch<Application>(`/applications/${id}/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admissions"] });
    },
  });
}
