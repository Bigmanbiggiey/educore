import { useMutation } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { InviteMemberInput, InviteMemberResult } from "../types";

// No list query to invalidate on success — `InviteMemberView` is a
// pure create action with no corresponding "members" list endpoint,
// unlike `useProvisionInstitution`'s institutions-list invalidation.
export function useInviteMember() {
  return useMutation({
    mutationFn: (input: InviteMemberInput) =>
      api.post<InviteMemberResult>("/members/invite/", input),
  });
}
