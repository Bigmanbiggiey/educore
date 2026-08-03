import { describe, expect, it } from "vitest";

import { convertToEnrollmentSchema } from "./convert-to-enrollment.schema";

const VALID_CLASS_GRADE_ID = "c1111111-1111-4111-8111-111111111111";
const VALID_TERM_ID = "51111111-1111-4111-8111-111111111111";
const VALID_STREAM_ID = "a1111111-1111-4111-8111-111111111111";

describe("convertToEnrollmentSchema", () => {
  it("accepts a payload without a stream", () => {
    const result = convertToEnrollmentSchema.safeParse({
      admission_number: "A-100",
      class_grade_id: VALID_CLASS_GRADE_ID,
      term_id: VALID_TERM_ID,
      stream_id: "",
    });
    expect(result.success).toBe(true);
  });

  it("accepts a payload with a stream", () => {
    const result = convertToEnrollmentSchema.safeParse({
      admission_number: "A-100",
      class_grade_id: VALID_CLASS_GRADE_ID,
      term_id: VALID_TERM_ID,
      stream_id: VALID_STREAM_ID,
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing admission number", () => {
    const result = convertToEnrollmentSchema.safeParse({
      admission_number: "",
      class_grade_id: VALID_CLASS_GRADE_ID,
      term_id: VALID_TERM_ID,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a class grade ID that isn't a valid UUID", () => {
    const result = convertToEnrollmentSchema.safeParse({
      admission_number: "A-100",
      class_grade_id: "not-a-uuid",
      term_id: VALID_TERM_ID,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a stream ID that isn't a valid UUID", () => {
    const result = convertToEnrollmentSchema.safeParse({
      admission_number: "A-100",
      class_grade_id: VALID_CLASS_GRADE_ID,
      term_id: VALID_TERM_ID,
      stream_id: "not-a-uuid",
    });
    expect(result.success).toBe(false);
  });
});
