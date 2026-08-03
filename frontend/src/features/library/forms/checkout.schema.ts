import { z } from "zod";

function isTodayOrLater(value: string): boolean {
  // Plain string comparison, not `Date` parsing — both sides are
  // zero-padded `YYYY-MM-DD`, which sorts identically to chronological
  // order, and sidesteps local-vs-UTC midnight mismatches entirely.
  const todayIso = new Date().toISOString().slice(0, 10);
  return value >= todayIso;
}

export const checkoutSchema = z.object({
  copy: z.string().uuid("Enter a valid copy ID"),
  borrower_type: z.union([z.literal("student"), z.literal("staff")]),
  borrower_id: z.string().uuid("Enter a valid borrower ID"),
  due_date: z
    .string()
    .min(1, "Choose a due date")
    .refine(isTodayOrLater, "Due date cannot be in the past"),
});

export type CheckoutFormValues = z.infer<typeof checkoutSchema>;
