import { describe, expect, it } from "vitest";

import { inviteMemberSchema } from "./invite-member.schema";

describe("inviteMemberSchema", () => {
  it("accepts a valid payload", () => {
    const result = inviteMemberSchema.safeParse({
      email: "teacher@stmary.ac.ke",
      role_name: "Teacher",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a missing email", () => {
    const result = inviteMemberSchema.safeParse({
      email: "",
      role_name: "Teacher",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = inviteMemberSchema.safeParse({
      email: "not-an-email",
      role_name: "Teacher",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a missing role", () => {
    const result = inviteMemberSchema.safeParse({
      email: "teacher@stmary.ac.ke",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a role that isn't one of the 11 invitable roles", () => {
    const result = inviteMemberSchema.safeParse({
      email: "teacher@stmary.ac.ke",
      role_name: "Institution Administrator",
    });
    expect(result.success).toBe(false);
  });
});
