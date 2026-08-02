import { Button } from "@/shared/components/Button";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { PAGE_SIZE, useRoutes } from "../api/useRoutes";
import type { Route } from "../types";

interface RoutesTableProps {
  page: number;
  onPageChange: (page: number) => void;
  onViewManifest: (routeId: string) => void;
}

export function RoutesTable({ page, onPageChange, onViewManifest }: RoutesTableProps) {
  const query = useRoutes(page);

  const columns = [
    { key: "name", header: "Route", render: (row: Route) => row.name },
    { key: "vehicle", header: "Vehicle", render: (row: Route) => row.vehicle },
    {
      key: "actions",
      header: "",
      render: (row: Route) => (
        <Button variant="outline" onClick={() => onViewManifest(row.id)}>
          View manifest
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
          emptyMessage="No routes set up yet."
          pagination={{ count: data.count, page, pageSize: PAGE_SIZE, onPageChange }}
        />
      )}
    </QueryBoundary>
  );
}
