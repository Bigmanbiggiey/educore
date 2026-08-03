import { z } from "zod";

function isNotInTheFuture(value: string): boolean {
  // Plain string comparison, not `Date` parsing — both sides are
  // zero-padded `YYYY-MM-DD`, which sorts identically to chronological
  // order, and sidesteps local-vs-UTC midnight mismatches entirely.
  const todayIso = new Date().toISOString().slice(0, 10);
  return value <= todayIso;
}

export const recordVisitSchema = z.object({
  student_id: z.string().uuid("Enter a valid student ID"),
  visit_date: z
    .string()
    .min(1, "Choose a visit date")
    .refine(isNotInTheFuture, "Visit date cannot be in the future"),
  treated_by_id: z.string().uuid("Enter a valid staff ID"),
  notes: z.string().optional(),
});

export type RecordVisitFormValues = z.infer<typeof recordVisitSchema>;
