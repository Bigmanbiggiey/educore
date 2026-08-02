import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { RecordPaymentInput } from "../types";

interface Payment {
  id: string;
}

export function useRecordPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RecordPaymentInput) => api.post<Payment>("/payments/", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["finance"] });
    },
  });
}
