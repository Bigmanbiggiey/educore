import { z } from "zod";

export const applicationDetailsSchema = z.object({
  first_name: z.string().min(1, "Enter a first name"),
  last_name: z.string().min(1, "Enter a last name"),
  term_applying_for_id: z.string().uuid("Enter a valid term ID"),
});

export type ApplicationDetailsFormValues = z.infer<typeof applicationDetailsSchema>;
