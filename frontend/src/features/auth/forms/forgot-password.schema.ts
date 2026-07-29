import { z } from "zod";

export const forgotPasswordSchema = z.object({
  emailOrPhone: z.string().min(1, "Enter your email or phone number."),
});

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;
