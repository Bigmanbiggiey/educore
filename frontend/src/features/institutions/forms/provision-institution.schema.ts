import { z } from "zod";

export const CURRICULUM_TYPE_OPTIONS = [
  { value: "cbc", label: "CBC" },
  { value: "844", label: "8-4-4" },
  { value: "british", label: "British" },
  { value: "tvet", label: "TVET" },
  { value: "university", label: "University" },
] as const;

export const provisionInstitutionSchema = z.object({
  name: z.string().min(1, "Enter an institution name"),
  slug: z
    .string()
    .min(1, "Enter a slug")
    .regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, and hyphens only"),
  curriculum_types: z
    .array(z.enum(["cbc", "844", "british", "tvet", "university"]))
    .min(1, "Select at least one curriculum"),
  timezone_name: z.string().optional(),
});

export type ProvisionInstitutionFormValues = z.infer<typeof provisionInstitutionSchema>;
