import { Modal } from "@/shared/components/Modal";
import { QueryBoundary } from "@/shared/components/QueryBoundary";
import { Table } from "@/shared/components/Table";

import { useRouteManifest } from "../api/useRouteManifest";
import type { RouteManifestEntry } from "../types";

interface ManifestModalProps {
  routeId: string | null;
  onClose: () => void;
}

const columns = [
  { key: "sequence", header: "#", render: (row: RouteManifestEntry) => row.sequence },
  { key: "name", header: "Stop", render: (row: RouteManifestEntry) => row.name },
  {
    key: "student_ids",
    header: "Students",
    render: (row: RouteManifestEntry) => row.student_ids.length,
  },
];

export function ManifestModal({ routeId, onClose }: ManifestModalProps) {
  const query = useRouteManifest(routeId);

  return (
    <Modal open={routeId !== null} onClose={onClose} title="Route manifest">
      <QueryBoundary query={query}>
        {(data) => (
          <Table
            columns={columns}
            rows={data}
            getRowKey={(row) => row.stop_id}
            emptyMessage="No stops on this route yet."
          />
        )}
      </QueryBoundary>
    </Modal>
  );
}
