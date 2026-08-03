import { describe, expect, it } from "vitest";

import { createStudentSchema } from "./create-student.schema";

describe("createStudentSchema", () => {
  it("accepts a minimal valid payload", () => {
    const result = createStudentSchema.safeParse({
      admission_number: "A-100",
      first_name: "Jane",
      last_name: "Doe",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing admission number", () => {
    const result = createStudentSchema.safeParse({
      admission_number: "",
      first_name: "Jane",
      last_name: "Doe",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing last name", () => {
    const result = createStudentSchema.safeParse({
      admission_number: "A-100",
      first_name: "Jane",
      last_name: "",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a past date of birth", () => {
    const result = createStudentSchema.safeParse({
      admission_number: "A-100",
      first_name: "Jane",
      last_name: "Doe",
      date_of_birth: "2015-01-01",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a date of birth in the future", () => {
    const result = createStudentSchema.safeParse({
      admission_number: "A-100",
      first_name: "Jane",
      last_name: "Doe",
      date_of_birth: "2099-01-01",
    });
    expect(result.success).toBe(false);
  });
});
