import type { components } from "@/shared/lib/api-types";

export type Student = components["schemas"]["Student"];
export type PaginatedStudents = components["schemas"]["PaginatedStudentList"];

// The generated `Student` schema doubles as both the read and write shape
// (openapi-typescript didn't split them here), which would otherwise force
// a create payload to also supply server-generated fields like `id`. This
// picks just what `POST /students/` actually needs.
export interface CreateStudentInput {
  admission_number: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  gender?: "male" | "female" | "";
}
