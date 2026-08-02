import { describe, expect, it } from "vitest";

import { allocateBedSchema } from "./allocate-bed.schema";

describe("allocateBedSchema", () => {
  it("accepts a valid payload", () => {
    expect(allocateBedSchema.safeParse({ student_id: "s-1" }).success).toBe(true);
  });

  it("rejects a missing student ID", () => {
    expect(allocateBedSchema.safeParse({ student_id: "" }).success).toBe(false);
  });
});
