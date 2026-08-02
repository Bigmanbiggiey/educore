import { z } from "zod";

export const recordVisitSchema = z.object({
  student_id: z.string().min(1, "Enter the student ID"),
  visit_date: z.string().min(1, "Choose a visit date"),
  treated_by_id: z.string().min(1, "Enter the treating nurse's staff ID"),
  notes: z.string().optional(),
});

export type RecordVisitFormValues = z.infer<typeof recordVisitSchema>;
