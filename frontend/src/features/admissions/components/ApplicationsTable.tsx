import { Badge } from "@/shared/components/Badge";
import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { PAGE_SIZE, useApplications } from "../api/useApplications";
import { useMakeOffer } from "../api/useMakeOffer";
import { applicantName, canMakeOffer, type Application } from "../types";

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
  onPageChange: (page: number) => void;
}

export function ApplicationsTable({ page, onPageChange }: ApplicationsTableProps) {
  const query = useApplications(page);
  const { mutate: makeOffer, isPending, variables: offeringId } = useMakeOffer();

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
      render: (row: Application) =>
        canMakeOffer(row) && (
          <Button
            variant="outline"
            disabled={isPending && offeringId === row.id}
            onClick={() => makeOffer(row.id)}
          >
            Make offer
          </Button>
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
          emptyMessage="No applications yet."
          pagination={{ count: data.count, page, pageSize: PAGE_SIZE, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
