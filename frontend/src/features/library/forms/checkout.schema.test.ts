import { describe, expect, it } from "vitest";

import { checkoutSchema } from "./checkout.schema";

function isoDate(daysFromToday: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromToday);
  return date.toISOString().slice(0, 10);
}

const VALID_COPY_ID = "c1111111-1111-4111-8111-111111111111";
const VALID_BORROWER_ID = "51111111-1111-4111-8111-111111111111";

describe("checkoutSchema", () => {
  it("accepts a valid payload", () => {
    const result = checkoutSchema.safeParse({
      copy: VALID_COPY_ID,
      borrower_type: "student",
      borrower_id: VALID_BORROWER_ID,
      due_date: isoDate(14),
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing copy ID", () => {
    const result = checkoutSchema.safeParse({
      copy: "",
      borrower_type: "student",
      borrower_id: VALID_BORROWER_ID,
      due_date: isoDate(14),
    });
    expect(result.success).toBe(false);
  });

  it("rejects a copy ID that isn't a valid UUID", () => {
    const result = checkoutSchema.safeParse({
      copy: "not-a-uuid",
      borrower_type: "student",
      borrower_id: VALID_BORROWER_ID,
      due_date: isoDate(14),
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid borrower type", () => {
    const result = checkoutSchema.safeParse({
      copy: VALID_COPY_ID,
      borrower_type: "guardian",
      borrower_id: VALID_BORROWER_ID,
      due_date: isoDate(14),
    });
    expect(result.success).toBe(false);
  });

  it("accepts today as the due date", () => {
    const result = checkoutSchema.safeParse({
      copy: VALID_COPY_ID,
      borrower_type: "student",
      borrower_id: VALID_BORROWER_ID,
      due_date: isoDate(0),
    });
    expect(result.success).toBe(true);
  });

  it("rejects a due date in the past", () => {
    const result = checkoutSchema.safeParse({
      copy: VALID_COPY_ID,
      borrower_type: "student",
      borrower_id: VALID_BORROWER_ID,
      due_date: isoDate(-1),
    });
    expect(result.success).toBe(false);
  });
});
