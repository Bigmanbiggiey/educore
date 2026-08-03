import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

export function useDeleteInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (invoiceId: string) => api.delete<void>(`/invoices/${invoiceId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["finance"] });
    },
  });
}
