import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { ParentDashboard } from "../types";

export function useParentDashboard() {
  return useQuery({
    queryKey: ["dashboard", "parent"],
    queryFn: () => api.get<ParentDashboard>("/dashboard/parent/"),
  });
}
