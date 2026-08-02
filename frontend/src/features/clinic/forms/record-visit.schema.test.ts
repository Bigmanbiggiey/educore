import { describe, expect, it } from "vitest";

import { recordVisitSchema } from "./record-visit.schema";

describe("recordVisitSchema", () => {
  it("accepts a minimal valid payload", () => {
    const result = recordVisitSchema.safeParse({
      student_id: "s-1",
      visit_date: "2026-08-01",
      treated_by_id: "n-1",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing student ID", () => {
    const result = recordVisitSchema.safeParse({
      student_id: "",
      visit_date: "2026-08-01",
      treated_by_id: "n-1",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing visit date", () => {
    const result = recordVisitSchema.safeParse({
      student_id: "s-1",
      visit_date: "",
      treated_by_id: "n-1",
    });
    expect(result.success).toBe(false);
  });
});
