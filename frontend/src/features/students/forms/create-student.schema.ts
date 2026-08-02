import { z } from "zod";

export const createStudentSchema = z.object({
  admission_number: z.string().min(1, "Enter an admission number"),
  first_name: z.string().min(1, "Enter a first name"),
  last_name: z.string().min(1, "Enter a last name"),
  date_of_birth: z.string().optional(),
  gender: z.union([z.literal("male"), z.literal("female"), z.literal("")]).optional(),
});

export type CreateStudentFormValues = z.infer<typeof createStudentSchema>;
