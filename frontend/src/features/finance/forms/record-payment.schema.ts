import { z } from "zod";

export const recordPaymentSchema = z.object({
  amount: z
    .string()
    .min(1, "Enter an amount")
    .refine((value) => Number(value) > 0, "Amount must be greater than zero"),
  method: z.union([z.literal("mpesa"), z.literal("cash"), z.literal("bank")]),
  reference: z.string().optional(),
  paid_at: z.string().min(1, "Enter when this payment was received"),
});

export type RecordPaymentFormValues = z.infer<typeof recordPaymentSchema>;
