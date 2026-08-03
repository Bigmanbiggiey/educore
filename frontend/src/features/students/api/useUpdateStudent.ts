import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { CreateStudentInput, Student } from "../types";

export function useUpdateStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: CreateStudentInput }) =>
      api.patch<Student>(`/students/${id}/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}
