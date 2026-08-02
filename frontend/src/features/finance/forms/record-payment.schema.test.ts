import { describe, expect, it } from "vitest";

import { recordPaymentSchema } from "./record-payment.schema";

describe("recordPaymentSchema", () => {
  it("accepts a valid payment", () => {
    const result = recordPaymentSchema.safeParse({
      amount: "500.00",
      method: "cash",
      paid_at: "2026-01-10T09:00",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a zero amount", () => {
    const result = recordPaymentSchema.safeParse({
      amount: "0",
      method: "cash",
      paid_at: "2026-01-10T09:00",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing paid_at", () => {
    const result = recordPaymentSchema.safeParse({ amount: "500", method: "cash", paid_at: "" });
    expect(result.success).toBe(false);
  });
});
