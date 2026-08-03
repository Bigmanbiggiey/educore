import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { ConvertToEnrollmentInput, EnrollmentResult } from "../types";

export function useConvertToEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ applicationId, input }: { applicationId: string; input: ConvertToEnrollmentInput }) =>
      api.post<EnrollmentResult>(`/applications/${applicationId}/convert-to-enrollment/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admissions"] });
    },
  });
}
