type QueryParams = Record<string, string | number | boolean | undefined>;

/** Drops `undefined`/empty-string values and returns a leading-`?`
 * querystring, or `""` if nothing is set. Replaces the hand-rolled
 * template-literal URL building every list hook used in Stage 3 — worth
 * extracting now that page/pageSize/ordering/filters multiply the
 * parameter count per hook. */
export function buildQueryString(params: QueryParams): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}
