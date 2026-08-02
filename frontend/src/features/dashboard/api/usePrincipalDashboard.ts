import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PrincipalDashboard } from "../types";

export function usePrincipalDashboard() {
  return useQuery({
    queryKey: ["dashboard", "principal"],
    queryFn: () => api.get<PrincipalDashboard>("/dashboard/principal/"),
  });
}
