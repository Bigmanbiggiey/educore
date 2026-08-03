import { useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";

import { AuditLogsScreen } from "@/features/audit-logs";
import { InstitutionsScreen } from "@/features/institutions";
import type { Institution } from "@/features/institutions";
import { Button } from "@/shared/components/Button";

interface SystemAdminOutletContext {
  actAs: (institutionId: string, institutionName: string) => Promise<void>;
}

type Tab = "institutions" | "audit-log";

export function DashboardPage() {
  const { actAs } = useOutletContext<SystemAdminOutletContext>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("institutions");

  async function handleActAs(institution: Institution) {
    await actAs(institution.id, institution.name);
    navigate("/institution-admin");
  }

  return (
    <div className="flex flex-col gap-4 p-6">
      <div className="flex gap-2">
        <Button
          variant={tab === "institutions" ? "primary" : "secondary"}
          onClick={() => setTab("institutions")}
        >
          Institutions
        </Button>
        <Button
          variant={tab === "audit-log" ? "primary" : "secondary"}
          onClick={() => setTab("audit-log")}
        >
          Audit log
        </Button>
      </div>
      {tab === "institutions" ? (
        <InstitutionsScreen onActAs={handleActAs} />
      ) : (
        <AuditLogsScreen />
      )}
    </div>
  );
}
