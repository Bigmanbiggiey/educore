import { describe, expect, it } from "vitest";

import { checkoutSchema } from "./checkout.schema";

describe("checkoutSchema", () => {
  it("accepts a valid payload", () => {
    const result = checkoutSchema.safeParse({
      copy: "c1111111-1111-1111-1111-111111111111",
      borrower_type: "student",
      borrower_id: "s1111111-1111-1111-1111-111111111111",
      due_date: "2026-08-15",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing copy ID", () => {
    const result = checkoutSchema.safeParse({
      copy: "",
      borrower_type: "student",
      borrower_id: "s1111111-1111-1111-1111-111111111111",
      due_date: "2026-08-15",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid borrower type", () => {
    const result = checkoutSchema.safeParse({
      copy: "c1111111-1111-1111-1111-111111111111",
      borrower_type: "guardian",
      borrower_id: "s1111111-1111-1111-1111-111111111111",
      due_date: "2026-08-15",
    });
    expect(result.success).toBe(false);
  });
});
