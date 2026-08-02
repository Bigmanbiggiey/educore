import type { components } from "@/shared/lib/api-types";

export type Route = components["schemas"]["Route"];
export type PaginatedRoutes = components["schemas"]["PaginatedRouteList"];

// `RouteViewSet.manifest` (backend/apps/transport/views.py) returns
// `RouteManifestEntrySerializer(many=True).data`, not a `Route` — the
// generated `v1_routes_manifest_retrieve` type is wrong because that action
// has no `@extend_schema` override, so drf-spectacular fell back to the
// viewset's default `Route` serializer. Typed by hand against the real
// serializer (backend/apps/transport/serializers.py) instead.
export interface RouteManifestEntry {
  stop_id: string;
  name: string;
  sequence: number;
  student_ids: string[];
}
