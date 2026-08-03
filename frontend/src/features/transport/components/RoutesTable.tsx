import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useRoutes } from "../api/useRoutes";
import type { Route } from "../types";

interface RoutesTableProps {
  page: number;
  pageSize: number;
  ordering?: string;
  search?: string;
  onPageChange: (page: number) => void;
  onViewManifest: (routeId: string) => void;
  onEdit: (route: Route) => void;
  onDelete: (route: Route) => void;
}

export function RoutesTable({
  page,
  pageSize,
  ordering,
  search,
  onPageChange,
  onViewManifest,
  onEdit,
  onDelete,
}: RoutesTableProps) {
  const query = useRoutes({ page, pageSize, ordering, search });

  const columns = [
    { key: "name", header: "Route", render: (row: Route) => row.name },
    { key: "vehicle", header: "Vehicle", render: (row: Route) => row.vehicle },
    {
      key: "actions",
      header: "",
      render: (row: Route) => (
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => onViewManifest(row.id)}>
            View manifest
          </Button>
          <Button variant="secondary" onClick={() => onEdit(row)}>
            Edit
          </Button>
          <Button variant="danger" onClick={() => onDelete(row)}>
            Delete
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
          emptyMessage="No routes set up yet."
          pagination={{ count: data.count, page, pageSize, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
