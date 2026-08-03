import { Badge } from "@/shared/components/Badge";
import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useInstitutions } from "../api/useInstitutions";
import type { Institution } from "../types";

interface InstitutionsTableProps {
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onManage: (institution: Institution) => void;
  onActAs: (institution: Institution) => void;
}

export function InstitutionsTable({
  page,
  pageSize,
  onPageChange,
  onManage,
  onActAs,
}: InstitutionsTableProps) {
  const query = useInstitutions({ page, pageSize });

  const columns = [
    { key: "name", header: "Name", render: (row: Institution) => row.name },
    { key: "slug", header: "Slug", render: (row: Institution) => row.slug },
    {
      key: "isolation_tier",
      header: "Isolation tier",
      render: (row: Institution) => row.isolation_tier,
    },
    {
      key: "is_active",
      header: "Status",
      render: (row: Institution) => (
        <Badge tone={row.is_active ? "success" : "neutral"}>
          {row.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (row: Institution) => (
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => onManage(row)}>
            Manage
          </Button>
          <Button variant="outline" onClick={() => onActAs(row)}>
            Act as
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
          emptyMessage="No institutions provisioned yet."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
