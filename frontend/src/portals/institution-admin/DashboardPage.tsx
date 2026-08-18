import { useState } from "react";

import { InviteMemberScreen } from "@/features/invite-member";
import { StudentsScreen } from "@/features/students";
import { Button } from "@/shared/components/Button";

type Tab = "students" | "invite-member";

export function DashboardPage() {
  const [tab, setTab] = useState<Tab>("students");

  return (
    <div className="flex flex-col gap-4 p-6">
      <div className="flex gap-2">
        <Button variant={tab === "students" ? "primary" : "secondary"} onClick={() => setTab("students")}>
          Students
        </Button>
        <Button
          variant={tab === "invite-member" ? "primary" : "secondary"}
          onClick={() => setTab("invite-member")}
        >
          Invite member
        </Button>
      </div>
      {tab === "students" ? <StudentsScreen /> : <InviteMemberScreen />}
    </div>
  );
}
