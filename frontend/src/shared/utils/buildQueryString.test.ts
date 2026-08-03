import { describe, expect, it } from "vitest";

import { buildQueryString } from "./buildQueryString";

describe("buildQueryString", () => {
  it("returns an empty string for no params", () => {
    expect(buildQueryString({})).toBe("");
  });

  it("drops undefined and empty-string values", () => {
    expect(buildQueryString({ page: 1, status: undefined, search: "" })).toBe("?page=1");
  });

  it("builds a leading-? querystring with multiple params", () => {
    const result = buildQueryString({ page: 2, page_size: 25, ordering: "-created_at" });
    expect(result).toBe("?page=2&page_size=25&ordering=-created_at");
  });

  it("stringifies booleans", () => {
    expect(buildQueryString({ returned: false })).toBe("?returned=false");
  });
});
