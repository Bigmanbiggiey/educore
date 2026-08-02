import { useState } from "react";

import { ManifestModal } from "./ManifestModal";
import { RoutesTable } from "./RoutesTable";

export function TransportScreen() {
  const [page, setPage] = useState(1);
  const [manifestRouteId, setManifestRouteId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Routes</h2>
      <RoutesTable page={page} onPageChange={setPage} onViewManifest={setManifestRouteId} />
      <ManifestModal routeId={manifestRouteId} onClose={() => setManifestRouteId(null)} />
    </div>
  );
}
