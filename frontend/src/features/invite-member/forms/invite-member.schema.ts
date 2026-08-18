import { z } from "zod";

// The 11 seeded roles an Institution Administrator may invite a member
// into (backend/apps/permissions/services.py's INVITABLE_ROLE_NAMES) —
// everything from app/portal-routing.ts's ROLE_TO_PORTAL_SLUG except
// "Institution Administrator" itself (auto-provisioned, never invited).
export const INVITABLE_ROLE_OPTIONS = [
  { value: "Principal", label: "Principal" },
  { value: "Deputy Principal", label: "Deputy Principal" },
  { value: "Finance Officer", label: "Finance Officer" },
  { value: "Teacher", label: "Teacher" },
  { value: "Parent", label: "Parent" },
  { value: "Student", label: "Student" },
  { value: "Librarian", label: "Librarian" },
  { value: "Nurse", label: "Nurse" },
  { value: "Receptionist", label: "Receptionist" },
  { value: "Transport Manager", label: "Transport Manager" },
  { value: "Hostel Warden", label: "Hostel Warden" },
] as const;

const INVITABLE_ROLE_VALUES = INVITABLE_ROLE_OPTIONS.map((option) => option.value);

export const inviteMemberSchema = z.object({
  email: z.string().min(1, "Enter an email address").email("Enter a valid email"),
  phone: z.string().optional(),
  role_name: z.enum(INVITABLE_ROLE_VALUES as [string, ...string[]], {
    invalid_type_error: "Select a role",
    required_error: "Select a role",
  }),
});

export type InviteMemberFormValues = z.infer<typeof inviteMemberSchema>;
