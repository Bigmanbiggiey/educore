import type { components } from "@/shared/lib/api-types";

export type Application = components["schemas"]["Application"];
export type PaginatedApplications = components["schemas"]["PaginatedApplicationList"];

const ELIGIBLE_FOR_OFFER: Application["stage"][] = ["submitted", "under_review"];

export function canMakeOffer(application: Application): boolean {
  return ELIGIBLE_FOR_OFFER.includes(application.stage);
}

export function canAcceptOffer(application: Application): boolean {
  return application.stage === "offered";
}

export function canConvertToEnrollment(application: Application): boolean {
  return application.stage === "accepted";
}

// `Application.applicant_details` is an unstructured JSON blob (name, DOB,
// guardian contact, etc — see the backend docstring) — this only reads the
// name-shaped keys `applicantName` already relies on, safely, for prefilling
// the edit form without assuming the object's full shape.
export function applicantDetailsRecord(application: Application): Record<string, unknown> {
  const details = application.applicant_details;
  return details && typeof details === "object" ? (details as Record<string, unknown>) : {};
}

export interface ConvertToEnrollmentInput {
  admission_number: string;
  class_grade_id: string;
  term_id: string;
  stream_id?: string;
}

export interface EnrollmentResult {
  enrollment_id: string;
}

export function applicantName(application: Application): string {
  const details = application.applicant_details;
  if (details && typeof details === "object") {
    const record = details as Record<string, unknown>;
    const name = record.name ?? [record.first_name, record.last_name].filter(Boolean).join(" ");
    if (typeof name === "string" && name.trim()) return name;
  }
  return "Unnamed applicant";
}
