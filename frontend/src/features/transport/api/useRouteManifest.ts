import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { RouteManifestEntry } from "../types";

export function useRouteManifest(routeId: string | null) {
  return useQuery({
    queryKey: ["transport", "manifest", routeId],
    queryFn: () => api.get<RouteManifestEntry[]>(`/routes/${routeId}/manifest/`),
    enabled: routeId !== null,
  });
}
