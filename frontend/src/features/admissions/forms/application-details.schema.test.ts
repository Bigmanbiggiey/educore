import { describe, expect, it } from "vitest";

import { applicationDetailsSchema } from "./application-details.schema";

const VALID_TERM_ID = "51111111-1111-4111-8111-111111111111";

describe("applicationDetailsSchema", () => {
  it("accepts a valid payload", () => {
    const result = applicationDetailsSchema.safeParse({
      first_name: "Jane",
      last_name: "Doe",
      term_applying_for_id: VALID_TERM_ID,
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing first name", () => {
    const result = applicationDetailsSchema.safeParse({
      first_name: "",
      last_name: "Doe",
      term_applying_for_id: VALID_TERM_ID,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a term ID that isn't a valid UUID", () => {
    const result = applicationDetailsSchema.safeParse({
      first_name: "Jane",
      last_name: "Doe",
      term_applying_for_id: "not-a-uuid",
    });
    expect(result.success).toBe(false);
  });
});
