import { useState } from "react";

import { Button } from "@/shared/components/Button";

import { InviteMemberModal } from "./InviteMemberModal";

// No list here, unlike `InstitutionsScreen` — `InviteMemberView` is a pure
// create action with no corresponding "members" list endpoint (that's
// each role's own owning app's job: staff/students/parents already have
// their own list views).
export function InviteMemberScreen() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Invite member</h2>
        <Button onClick={() => setModalOpen(true)}>Invite member</Button>
      </div>
      <p className="text-sm text-text/70">
        Creates a login and assigns a role at this institution. The new member sets their own
        password via the reset link sent to their email.
      </p>
      <InviteMemberModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
