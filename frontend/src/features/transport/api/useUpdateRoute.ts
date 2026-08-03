import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { Route } from "../types";
import type { RouteFormValues } from "../forms/route.schema";

export function useUpdateRoute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: RouteFormValues }) =>
      api.patch<Route>(`/routes/${id}/`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["transport"] });
    },
  });
}
