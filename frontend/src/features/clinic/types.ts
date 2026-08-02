import type { components } from "@/shared/lib/api-types";

export type ClinicVisit = components["schemas"]["ClinicVisit"];
export type PaginatedClinicVisits = components["schemas"]["PaginatedClinicVisitList"];

export interface RecordVisitInput {
  student_id: string;
  visit_date: string;
  treated_by_id: string;
  notes?: string;
}
