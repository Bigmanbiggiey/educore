/**
 * Role name → portal slug, for the post-login redirect / portal picker
 * (docs/frontend-architecture.md §1). Covers the 12 seeded institution
 * roles (backend/apps/permissions's 0002 data migration) — "Deputy
 * Principal" shares the Principal portal, there's no separate one.
 *
 * "System Administrator" is deliberately absent: it's granted via
 * `is_platform_staff`, not an `InstitutionMembership`/role
 * (docs/permissions.md §7's "break glass" model), so it never appears in
 * `/api/v1/auth/me/`'s `institution_membership.roles`. The `system-admin`
 * portal folder exists for structural completeness but isn't wired into
 * this map or the router yet — building is_platform_staff detection on
 * the frontend is out of scope until the backend's break-glass flow is.
 */
export const ROLE_TO_PORTAL_SLUG: Record<string, string> = {
  "Institution Administrator": "institution-admin",
  Principal: "principal",
  "Deputy Principal": "principal",
  "Finance Officer": "finance-officer",
  Teacher: "teacher",
  Parent: "parent",
  Student: "student",
  Librarian: "librarian",
  Nurse: "nurse",
  Receptionist: "receptionist",
  "Transport Manager": "transport-manager",
  "Hostel Warden": "hostel-warden",
};

export const PORTAL_DISPLAY_NAMES: Record<string, string> = {
  "institution-admin": "Institution Administrator",
  principal: "Principal",
  "finance-officer": "Finance Officer",
  teacher: "Teacher",
  parent: "Parent",
  student: "Student",
  librarian: "Librarian",
  nurse: "Nurse",
  receptionist: "Receptionist",
  "transport-manager": "Transport Manager",
  "hostel-warden": "Hostel Warden",
};

/** De-duplicated, since "Principal" and "Deputy Principal" both resolve to
 * the same portal — a Deputy Principal who also teaches shouldn't see two
 * "principal" entries in the picker. */
export function portalSlugsForRoles(roles: string[]): string[] {
  const slugs = new Set<string>();
  for (const role of roles) {
    const slug = ROLE_TO_PORTAL_SLUG[role];
    if (slug) slugs.add(slug);
  }
  return [...slugs];
}
