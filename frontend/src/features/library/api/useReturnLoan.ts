import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Loan } from "../types";

export function useReturnLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (loanId: string) => api.post<Loan>(`/loans/${loanId}/return/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["library"] });
    },
  });
}
