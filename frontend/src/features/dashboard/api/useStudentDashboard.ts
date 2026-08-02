import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { StudentDashboard } from "../types";

export function useStudentDashboard() {
  return useQuery({
    queryKey: ["dashboard", "student"],
    queryFn: () => api.get<StudentDashboard>("/dashboard/student/"),
  });
}
