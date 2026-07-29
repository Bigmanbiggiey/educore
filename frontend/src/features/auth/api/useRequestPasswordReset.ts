import { useMutation } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

interface RequestPasswordResetInput {
  emailOrPhone: string;
}

interface RequestPasswordResetResponse {
  detail: string;
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: ({ emailOrPhone }: RequestPasswordResetInput) =>
      api.post<RequestPasswordResetResponse>("/auth/password-reset/request/", {
        email_or_phone: emailOrPhone,
      }),
  });
}
