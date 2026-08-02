import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { TeacherDashboard } from "../types";

export function useTeacherDashboard() {
  return useQuery({
    queryKey: ["dashboard", "teacher"],
    queryFn: () => api.get<TeacherDashboard>("/dashboard/teacher/"),
  });
}
