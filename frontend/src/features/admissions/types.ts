import type { components } from "@/shared/lib/api-types";

export type Application = components["schemas"]["Application"];
export type PaginatedApplications = components["schemas"]["PaginatedApplicationList"];

const ELIGIBLE_FOR_OFFER: Application["stage"][] = ["submitted", "under_review"];

export function canMakeOffer(application: Application): boolean {
  return ELIGIBLE_FOR_OFFER.includes(application.stage);
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
