import type { components } from "@/shared/lib/api-types";

export type Institution = components["schemas"]["Institution"];
export type PaginatedInstitutions = components["schemas"]["PaginatedInstitutionList"];
export type Domain = components["schemas"]["Domain"];
export type CurriculumType = components["schemas"]["CurriculumTypeEnum"];
export type IsolationTier = components["schemas"]["IsolationTierEnum"];

export interface ProvisionInstitutionInput {
  name: string;
  slug: string;
  curriculum_types: CurriculumType[];
  timezone_name?: string;
  admin_email: string;
  admin_phone?: string;
}

export interface SetIsolationTierInput {
  tier: IsolationTier;
  db_alias?: string;
}

export interface AddCustomDomainInput {
  hostname: string;
}

export interface VerifyDomainInput {
  resolved_txt_records: string[];
}
