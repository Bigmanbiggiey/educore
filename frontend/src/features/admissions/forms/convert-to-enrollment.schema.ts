import { z } from "zod";

function optionalUuid(message: string) {
  return z.preprocess(
    (value) => (value === "" ? undefined : value),
    z.string().uuid(message).optional(),
  );
}

export const convertToEnrollmentSchema = z.object({
  admission_number: z.string().min(1, "Enter an admission number"),
  class_grade_id: z.string().uuid("Enter a valid class grade ID"),
  term_id: z.string().uuid("Enter a valid term ID"),
  stream_id: optionalUuid("Enter a valid stream ID"),
});

export type ConvertToEnrollmentFormValues = z.infer<typeof convertToEnrollmentSchema>;
