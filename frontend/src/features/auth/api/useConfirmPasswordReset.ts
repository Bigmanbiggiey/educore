import { useMutation } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

interface ConfirmPasswordResetInput {
  token: string;
  newPassword: string;
}

interface ConfirmPasswordResetResponse {
  detail: string;
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: ({ token, newPassword }: ConfirmPasswordResetInput) =>
      api.post<ConfirmPasswordResetResponse>("/auth/password-reset/confirm/", {
        token,
        new_password: newPassword,
      }),
  });
}
