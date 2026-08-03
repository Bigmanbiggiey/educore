import { describe, expect, it } from "vitest";

import { recordVisitSchema } from "./record-visit.schema";

function isoDate(daysFromToday: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromToday);
  return date.toISOString().slice(0, 10);
}

const VALID_STUDENT_ID = "51111111-1111-4111-8111-111111111111";
const VALID_STAFF_ID = "c1111111-1111-4111-8111-111111111111";

describe("recordVisitSchema", () => {
  it("accepts a minimal valid payload", () => {
    const result = recordVisitSchema.safeParse({
      student_id: VALID_STUDENT_ID,
      visit_date: isoDate(0),
      treated_by_id: VALID_STAFF_ID,
    });
    expect(result.success).toBe(true);
  });

  it("rejects a student ID that isn't a valid UUID", () => {
    const result = recordVisitSchema.safeParse({
      student_id: "not-a-uuid",
      visit_date: isoDate(0),
      treated_by_id: VALID_STAFF_ID,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing visit date", () => {
    const result = recordVisitSchema.safeParse({
      student_id: VALID_STUDENT_ID,
      visit_date: "",
      treated_by_id: VALID_STAFF_ID,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a visit date in the future", () => {
    const result = recordVisitSchema.safeParse({
      student_id: VALID_STUDENT_ID,
      visit_date: isoDate(1),
      treated_by_id: VALID_STAFF_ID,
    });
    expect(result.success).toBe(false);
  });

  it("accepts a visit date in the past", () => {
    const result = recordVisitSchema.safeParse({
      student_id: VALID_STUDENT_ID,
      visit_date: isoDate(-30),
      treated_by_id: VALID_STAFF_ID,
    });
    expect(result.success).toBe(true);
  });
});
