import { useState } from "react";

import { ConfirmModal } from "@/shared/components/ConfirmModal";
import { Select } from "@/shared/components/Select";
import { TextField } from "@/shared/components/TextField";

import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from "../api/useRoutes";
import { useDeleteRoute } from "../api/useDeleteRoute";
import type { Route } from "../types";
import { EditRouteModal } from "./EditRouteModal";
import { ManifestModal } from "./ManifestModal";
import { RoutesTable } from "./RoutesTable";

const SORT_OPTIONS = [
  { value: "", label: "Default order" },
  { value: "name", label: "Name (A–Z)" },
  { value: "-name", label: "Name (Z–A)" },
];

const PAGE_SIZE_SELECT_OPTIONS = PAGE_SIZE_OPTIONS.map((size) => ({
  value: String(size),
  label: `${size} per page`,
}));

export function TransportScreen() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [ordering, setOrdering] = useState("");
  const [search, setSearch] = useState("");
  const [manifestRouteId, setManifestRouteId] = useState<string | null>(null);
  const [editingRoute, setEditingRoute] = useState<Route | null>(null);
  const [deletingRoute, setDeletingRoute] = useState<Route | null>(null);

  const { mutate: deleteRoute, isPending: isDeleting } = useDeleteRoute();

  function handleConfirmDelete() {
    if (!deletingRoute) return;
    deleteRoute(deletingRoute.id, { onSuccess: () => setDeletingRoute(null) });
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-text">Routes</h2>
      <div className="flex flex-wrap gap-4">
        <TextField
          label="Search"
          name="search"
          placeholder="Route name or vehicle registration"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
        />
        <Select
          label="Sort by"
          name="sort-by"
          options={SORT_OPTIONS}
          value={ordering}
          onChange={(event) => {
            setOrdering(event.target.value);
            setPage(1);
          }}
        />
        <Select
          label="Page size"
          name="page-size"
          options={PAGE_SIZE_SELECT_OPTIONS}
          value={String(pageSize)}
          onChange={(event) => {
            setPageSize(Number(event.target.value));
            setPage(1);
          }}
        />
      </div>
      <RoutesTable
        page={page}
        pageSize={pageSize}
        ordering={ordering || undefined}
        search={search || undefined}
        onPageChange={setPage}
        onViewManifest={setManifestRouteId}
        onEdit={setEditingRoute}
        onDelete={setDeletingRoute}
      />
      <ManifestModal routeId={manifestRouteId} onClose={() => setManifestRouteId(null)} />
      <EditRouteModal route={editingRoute} onClose={() => setEditingRoute(null)} />
      <ConfirmModal
        open={deletingRoute !== null}
        title="Delete route"
        message={deletingRoute ? `Delete route "${deletingRoute.name}"? This cannot be undone.` : ""}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeletingRoute(null)}
        isConfirming={isDeleting}
      />
    </div>
  );
}
