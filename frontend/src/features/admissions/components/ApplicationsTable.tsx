import { Badge } from "@/shared/components/Badge";
import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useAcceptOffer } from "../api/useAcceptOffer";
import { useApplications } from "../api/useApplications";
import { useMakeOffer } from "../api/useMakeOffer";
import {
  applicantName,
  canAcceptOffer,
  canConvertToEnrollment,
  canMakeOffer,
  type Application,
} from "../types";

const STAGE_TONE: Record<Application["stage"], "neutral" | "success" | "warning" | "danger"> = {
  submitted: "neutral",
  under_review: "warning",
  offered: "success",
  accepted: "success",
  enrolled: "success",
  rejected: "danger",
  withdrawn: "danger",
};

interface ApplicationsTableProps {
  page: number;
  pageSize: number;
  ordering?: string;
  stage?: Application["stage"];
  onPageChange: (page: number) => void;
  onConvertToEnrollment: (applicationId: string) => void;
  onEdit: (application: Application) => void;
}

export function ApplicationsTable({
  page,
  pageSize,
  ordering,
  stage,
  onPageChange,
  onConvertToEnrollment,
  onEdit,
}: ApplicationsTableProps) {
  const query = useApplications({ page, pageSize, ordering, stage });
  const { mutate: makeOffer, isPending: isMakingOffer, variables: offeringId } = useMakeOffer();
  const { mutate: acceptOffer, isPending: isAccepting, variables: acceptingId } = useAcceptOffer();

  const columns = [
    { key: "applicant", header: "Applicant", render: (row: Application) => applicantName(row) },
    {
      key: "stage",
      header: "Stage",
      render: (row: Application) => <Badge tone={STAGE_TONE[row.stage]}>{row.stage}</Badge>,
    },
    {
      key: "actions",
      header: "",
      render: (row: Application) => (
        <div className="flex gap-2">
          {canMakeOffer(row) && (
            <Button
              variant="outline"
              disabled={isMakingOffer && offeringId === row.id}
              onClick={() => makeOffer(row.id)}
            >
              Make offer
            </Button>
          )}
          {canAcceptOffer(row) && (
            <Button
              variant="outline"
              disabled={isAccepting && acceptingId === row.id}
              onClick={() => acceptOffer(row.id)}
            >
              Accept offer
            </Button>
          )}
          {canConvertToEnrollment(row) && (
            <Button variant="outline" onClick={() => onConvertToEnrollment(row.id)}>
              Convert to enrollment
            </Button>
          )}
          <Button variant="secondary" onClick={() => onEdit(row)}>
            Edit
          </Button>
        </div>
      ),
    },
  ];

  return (
    <QueryBoundary query={query}>
      {(data) => (
        <Table
          columns={columns}
          rows={data.results}
          getRowKey={(row) => row.id}
          emptyMessage="No applications match these filters."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
