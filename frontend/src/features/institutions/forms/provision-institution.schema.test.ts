import { describe, expect, it } from "vitest";

import { provisionInstitutionSchema } from "./provision-institution.schema";

describe("provisionInstitutionSchema", () => {
  it("accepts a valid payload", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "st-mary",
      curriculum_types: ["cbc"],
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing name", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "",
      slug: "st-mary",
      curriculum_types: ["cbc"],
    });
    expect(result.success).toBe(false);
  });

  it("rejects a slug with uppercase or spaces", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "St Mary",
      curriculum_types: ["cbc"],
    });
    expect(result.success).toBe(false);
  });

  it("rejects an empty curriculum selection", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "st-mary",
      curriculum_types: [],
    });
    expect(result.success).toBe(false);
  });
});
