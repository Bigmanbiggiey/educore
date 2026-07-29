import { z } from "zod";

// min(10) mirrors the backend's MinimumLengthValidator
// (docs/authentication.md §5) for fast feedback — the server re-validates
// this and the rest of Django's password validators regardless; this
// schema is UX only, never the security boundary.
export const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(10, "Password must be at least 10 characters."),
    confirmPassword: z.string().min(1, "Confirm your new password."),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: "Passwords don't match.",
    path: ["confirmPassword"],
  });

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;
