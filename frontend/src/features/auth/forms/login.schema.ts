import { z } from "zod";

// Client-side validation is a UX layer only — the server is the actual
// source of truth (docs/frontend-architecture.md §4). It doesn't try to
// distinguish an email from a phone number; the backend already accepts
// either under one field (accounts.selectors.get_user_by_email_or_phone).
export const loginSchema = z.object({
  emailOrPhone: z.string().min(1, "Enter your email or phone number."),
  password: z.string().min(1, "Enter your password."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
