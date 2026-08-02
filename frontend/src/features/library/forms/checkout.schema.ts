import { z } from "zod";

export const checkoutSchema = z.object({
  copy: z.string().min(1, "Enter the copy ID"),
  borrower_type: z.union([z.literal("student"), z.literal("staff")]),
  borrower_id: z.string().min(1, "Enter the borrower ID"),
  due_date: z.string().min(1, "Choose a due date"),
});

export type CheckoutFormValues = z.infer<typeof checkoutSchema>;
