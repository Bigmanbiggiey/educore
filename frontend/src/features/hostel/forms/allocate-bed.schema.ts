import { z } from "zod";

export const allocateBedSchema = z.object({
  student_id: z.string().min(1, "Enter the student ID"),
});

export type AllocateBedFormValues = z.infer<typeof allocateBedSchema>;
