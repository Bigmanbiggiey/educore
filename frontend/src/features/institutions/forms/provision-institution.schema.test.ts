import { describe, expect, it } from "vitest";

import { provisionInstitutionSchema } from "./provision-institution.schema";

describe("provisionInstitutionSchema", () => {
  it("accepts a valid payload", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "st-mary",
      curriculum_types: ["cbc"],
      admin_email: "admin@stmary.ac.ke",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing name", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "",
      slug: "st-mary",
      curriculum_types: ["cbc"],
      admin_email: "admin@stmary.ac.ke",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a slug with uppercase or spaces", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "St Mary",
      curriculum_types: ["cbc"],
      admin_email: "admin@stmary.ac.ke",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an empty curriculum selection", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "st-mary",
      curriculum_types: [],
      admin_email: "admin@stmary.ac.ke",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing administrator email", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "st-mary",
      curriculum_types: ["cbc"],
      admin_email: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid administrator email", () => {
    const result = provisionInstitutionSchema.safeParse({
      name: "St Mary",
      slug: "st-mary",
      curriculum_types: ["cbc"],
      admin_email: "not-an-email",
    });
    expect(result.success).toBe(false);
  });
});
