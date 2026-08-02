import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/lib/api";

import type { PaginatedTerms, Term } from "../types";

/** No `is_current` query filter on `/terms/` (see the generated
 * `v1_terms_list` query params), so the current term is resolved client-side
 * from a single unpaginated fetch — the same "resolve current term" need
 * `hostel`'s occupancy screen and this feature both have. */
export function useCurrentTerm() {
  return useQuery({
    queryKey: ["academic-terms", "current"],
    queryFn: async () => {
      const data = await api.get<PaginatedTerms>("/terms/?page_size=100");
      return data.results.find((term) => term.is_current) ?? null;
    },
  });
}

export type { Term };
